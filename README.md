# IFS-Gradient-GEN
A desktop app for creating, editing, and exporting .gradient files compatible with IFS-based renderers like JWildfire. Features include a visual gradient editor, color wheel, RGB sliders, and one-click export to a 288-step compatible format.
# IFS Gradient Editor 🎨

A desktop app for designing, editing, and exporting gradient color maps (`.gradient`) compatible with **IFS-based renderers** such as **JWildfire**, **Apophysis**, or any custom fractal software that uses 288-step gradients.

---

## 🔥 Features

### 🎚️ Gradient Stop Editor
- Click on the gradient bar to select a stop
- Add or remove stops with buttons
- Visual indicators show stop positions  
![Stop Editor](screenshots/gradient-stops.png)

---

### 🖍️ Color Editing Panel
- Adjust selected stop's RGB values with sliders
- Preview color in real time  
![Color Sliders](screenshots/color-sliders.png)

---

### 🎨 Color Wheel Picker
- Use the native color wheel to quickly choose any color
- Updates selected stop automatically  
![Color Picker](screenshots/color-picker.png)

---

### 🧭 Position Control
- Use the position slider to move the stop along the gradient line  
![Position Slider](screenshots/position-slider.png)

---

### 💾 Save / Load
- Save gradients as `.gradient` files compatible with **JWildfire**
- Load any existing `.gradient` file back into the editor  
![Save Dialog](screenshots/save-gradient.png)

---

## ⚙️ Installation & Setup

### 💻 Run from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/PRASADSHINDE117/IFS-Gradient-GEN.git
   cd IFS-Gradient-GEN
2. bulid:
   ```bash 
   pip install pyinstaller
   pyinstaller --onefile --windowed --icon=icon.ico main.py
