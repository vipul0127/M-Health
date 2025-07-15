import numpy as np
import matplotlib.pyplot as plt

# Simulate a PPG signal
np.random.seed(42)  # For reproducibility
t = np.linspace(0, 10, 1000)  # Time points (seconds)
freq = 1.0  # Heart rate ~60 bpm (1 Hz)
ppg_signal = np.sin(2 * np.pi * freq * t) + 0.2 * np.random.normal(0, 0.1, t.size)  # Sine wave + noise

# Create the plot
plt.figure(figsize=(10, 4))
plt.plot(t, ppg_signal, color='red', linewidth=2)  # Red line for PPG signal

# Customize the plot
plt.title('PPG Signal', color='white', fontsize=14)
plt.xlabel('Time (seconds)', color='white', fontsize=12)
plt.ylabel('Amplitude', color='white', fontsize=12)

# Set black background and customize axes
plt.style.use('dark_background')
ax = plt.gca()
ax.set_facecolor('black')
ax.spines['top'].set_color('white')
ax.spines['right'].set_color('white')
ax.spines['left'].set_color('white')
ax.spines['bottom'].set_color('white')
ax.tick_params(colors='white')

# Save the image
plt.savefig('ppg_graph.png', dpi=300, bbox_inches='tight', facecolor='black')
plt.close()