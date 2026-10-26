import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

# ==========================================
# 1. System Dynamics & Matrix Setup
# ==========================================
dt = 1.0  

F = np.array([[1, 0, dt, 0],
              [0, 1, 0, dt],
              [0, 0, 1, 0],
              [0, 0, 0, 1]])

H = np.array([[1, 0, 0, 0],
              [0, 1, 0, 0]])

q_var = 0.1
Q = np.array([[q_var, 0, 0, 0],
              [0, q_var, 0, 0],
              [0, 0, q_var, 0],
              [0, 0, 0, q_var]])

r_var = 50.0
R = np.array([[r_var, 0],
              [0, r_var]])

# Global state variables
frame_count = 0
is_paused = False

def reset_state():
    """Resets all simulation variables and history."""
    global true_state, x_est, P_est, frame_count
    global hist_true_x, hist_true_y, hist_meas_x, hist_meas_y, hist_est_x, hist_est_y
    
    frame_count = 0
    true_state = np.array([[0], [0], [2], [2]]) 
    x_est = np.array([[0], [0], [2], [2]])
    P_est = np.eye(4) * 10
    
    hist_true_x, hist_true_y = [], []
    hist_meas_x, hist_meas_y = [], []
    hist_est_x, hist_est_y = [], []

reset_state()

# ==========================================
# 2. Animation & Plotting Setup
# ==========================================
fig, (ax_plot, ax_text) = plt.subplots(1, 2, figsize=(14, 7), gridspec_kw={'width_ratios': [2, 1]})
fig.canvas.manager.set_window_title('Kalman Filter 2D Kinematic Tracking')
plt.subplots_adjust(bottom=0.2)  # Make room for buttons

ax_plot.set_xlim(-10, 100)
ax_plot.set_ylim(-10, 100)
ax_plot.set_title("Drone Radar Tracking (True vs Measured vs Estimated)")
ax_plot.set_xlabel("X Position")
ax_plot.set_ylabel("Y Position")
ax_plot.grid(True, linestyle='--', alpha=0.6)

true_line, = ax_plot.plot([], [], 'g-', label='True Path', alpha=0.5, linewidth=2)
meas_scatter = ax_plot.scatter([], [], c='r', marker='x', label='Noisy Radar Measurement', alpha=0.6)
est_line, = ax_plot.plot([], [], 'b-', label='Kalman Filter Estimate', linewidth=2)
ax_plot.legend(loc='upper left')

ax_text.axis('off')
ax_text.set_title("Live Calculations", fontweight='bold')
calc_text = ax_text.text(0.0, 0.95, "", va='top', ha='left', fontsize=11, family='monospace')

# ==========================================
# 3. The Main Kalman Filter Loop
# ==========================================
def update(frame=None):
    global true_state, x_est, P_est, frame_count
    
    frame_count += 1
    
    # --- SIMULATE THE REAL WORLD ---
    process_noise = np.random.multivariate_normal([0,0,0,0], Q).reshape(4,1)
    true_state = F @ true_state + process_noise
    
    measurement_noise = np.random.multivariate_normal([0,0], R).reshape(2,1)
    z = H @ true_state + measurement_noise
    
    # --- PRESENTER 1: PREDICTION ---
    x_pred = F @ x_est
    P_pred = F @ P_est @ F.T + Q
    
    # --- PRESENTER 2: MEASUREMENT UPDATE ---
    z_pred = H @ x_pred
    innovation = z - z_pred
    S = H @ P_pred @ H.T + R
    K = P_pred @ H.T @ np.linalg.inv(S)
    x_est = x_pred + K @ innovation
    P_est = P_pred - K @ S @ K.T
    
    # --- UPDATE VISUALS ---
    hist_true_x.append(true_state[0,0])
    hist_true_y.append(true_state[1,0])
    hist_meas_x.append(z[0,0])
    hist_meas_y.append(z[1,0])
    hist_est_x.append(x_est[0,0])
    hist_est_y.append(x_est[1,0])
    
    true_line.set_data(hist_true_x, hist_true_y)
    meas_scatter.set_offsets(np.c_[hist_meas_x, hist_meas_y])
    est_line.set_data(hist_est_x, hist_est_y)
    
    # Pan camera
    if true_state[0,0] > ax_plot.get_xlim()[1] - 10:
        ax_plot.set_xlim(ax_plot.get_xlim()[0] + 20, ax_plot.get_xlim()[1] + 20)
    if true_state[1,0] > ax_plot.get_ylim()[1] - 10:
        ax_plot.set_ylim(ax_plot.get_ylim()[0] + 20, ax_plot.get_ylim()[1] + 20)

    display_text = (
        f"Time Step (k): {frame_count}\n"
        f"-----------------------------------\n"
        f"Actual Radar Measurement (z):\n"
        f"  X: {z[0,0]:.2f}, Y: {z[1,0]:.2f}\n\n"
        
        f"Predicted Measurement (z_hat):\n"
        f"  X: {z_pred[0,0]:.2f}, Y: {z_pred[1,0]:.2f}\n\n"
        
        f"Innovation (z - z_hat):\n"
        f"  dx: {innovation[0,0]:.2f}\n"
        f"  dy: {innovation[1,0]:.2f}\n\n"
        
        f"Innovation Covariance (S):\n"
        f"  | {S[0,0]:.1f}  {S[0,1]:.1f} |\n"
        f"  | {S[1,0]:.1f}  {S[1,1]:.1f} |\n\n"
        
        f"Kalman Gain (K) [Pos X, Y]:\n"
        f"  K_x: {K[0,0]:.3f}\n"
        f"  K_y: {K[1,1]:.3f}\n\n"
        
        f"Corrected State Estimate:\n"
        f"  X Pos: {x_est[0,0]:.2f}\n"
        f"  Y Pos: {x_est[1,0]:.2f}\n"
    )
    calc_text.set_text(display_text)
    
    return true_line, meas_scatter, est_line, calc_text

# ==========================================
# 4. Interactive Controls (Buttons)
# ==========================================
ax_pause = plt.axes([0.15, 0.05, 0.1, 0.075])
ax_play = plt.axes([0.3, 0.05, 0.1, 0.075])
ax_step = plt.axes([0.45, 0.05, 0.1, 0.075])
ax_restart = plt.axes([0.6, 0.05, 0.1, 0.075])

btn_pause = Button(ax_pause, 'Pause')
btn_play = Button(ax_play, 'Continue')
btn_step = Button(ax_step, 'Manual Step')
btn_restart = Button(ax_restart, 'Restart')

def pause(event):
    global is_paused
    ani.pause()
    is_paused = True

def play(event):
    global is_paused
    ani.resume()
    is_paused = False

def step(event):
    if is_paused:
        update()
        fig.canvas.draw_idle()

def restart(event):
    reset_state()
    
    # Reset plot limits and clear lines
    ax_plot.set_xlim(-10, 100)
    ax_plot.set_ylim(-10, 100)
    true_line.set_data([], [])
    meas_scatter.set_offsets(np.empty((0, 2)))
    est_line.set_data([], [])
    calc_text.set_text("")
    
    fig.canvas.draw_idle()

btn_pause.on_clicked(pause)
btn_play.on_clicked(play)
btn_step.on_clicked(step)
btn_restart.on_clicked(restart)

# Start animation (increased interval to 500ms to make default speed more readable)
ani = animation.FuncAnimation(fig, update, interval=500, blit=False, save_count=200)

plt.show()