"""Paired radar uncertainty sweep; bootstrap entire trajectories, not time steps."""
import json
from pathlib import Path
import numpy as np
from benchmark_filters import INITIAL,F,G,R,P0,UKF_KAPPA,observe,wrap,cycle

def main():
    rng=np.random.default_rng(20261023)
    runs,steps=300,30
    # Common standardized randomness across uncertainty levels and methods.
    initial=rng.normal(size=(runs,4))
    acceleration=rng.normal(0,.5,size=(runs,steps,2))
    noise=rng.normal(size=(runs,steps,2)) @ np.linalg.cholesky(R).T
    bootstrap=rng.integers(0,runs,size=(2000,runs))
    results=[]
    for sd in [25,50,100,200,400,600,800,1000,1200]:
        prior=P0.copy();prior[:2,:2]=np.eye(2)*sd**2
        losses={m:[] for m in ['EKF','UKF','CKF']}
        failures={m:0 for m in losses}
        for r in range(runs):
            truth=INITIAL+np.linalg.cholesky(prior)@initial[r]
            estimates={m:(INITIAL.copy(),prior.copy()) for m in losses}
            errors={m:[] for m in losses}
            for k in range(steps):
                truth=F@truth+G@acceleration[r,k]
                z=observe(truth[None,:])[0]+noise[r,k];z[1]=wrap(z[1])
                for m in losses:
                    if estimates[m] is None: continue
                    try:
                        estimates[m]=cycle(*estimates[m],z,m)
                        if not all(np.all(np.isfinite(v)) for v in estimates[m]): raise ValueError('nonfinite')
                        errors[m].append(float(np.sum((estimates[m][0][:2]-truth[:2])**2)))
                    except (ValueError,np.linalg.LinAlgError):
                        failures[m]+=1;estimates[m]=None
            for m in losses: losses[m].append(np.mean(errors[m]) if estimates[m] is not None else np.nan)
        row={'position_sd_m':sd,'methods':{}}
        for m,v in losses.items():
            v=np.array(v)
            if failures[m]: raise RuntimeError(f'{sd} {m}: {failures[m]} failures; do not silently omit')
            boot=np.sqrt(v[bootstrap].mean(axis=1))
            row['methods'][m]={'rmse_m':float(np.sqrt(v.mean())),'ci95_m':np.percentile(boot,[2.5,97.5]).tolist(),'failures':failures[m]}
        results.append(row)
    out={'seed':20261023,'runs':runs,'steps':steps,'bootstrap_samples':2000,'ukf':{'alpha':1,'beta':2,'kappa':UKF_KAPPA},'metric':'Position RMSE pooled over first 30 updates; 95% percentile bootstrap over trajectories','results':results}
    Path(__file__).with_name('uncertainty-results.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(out))
if __name__=='__main__':main()
