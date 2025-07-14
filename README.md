# IFS-Gradient-GEN
A desktop app for creating, editing, and exporting .gradient files compatible with IFS-based renderers like JWildfire. Features include a visual gradient editor, color wheel, RGB sliders, and one-click export to a 288-step compatible format.

## ⬇️ Download

You can download the latest version of the standalone app for Windows here:

🔗 [Download Gradient Editor (.exe)](https://github.com/PRASADSHINDE117/IFS-Gradient-GEN/releases/latest)

# IFS Gradient Editor 🎨

![GUI]("C:\Users\Prasad\Pictures\Screenshots\gui.png")

A desktop app for designing, editing, and exporting gradient color maps (`.gradient`) compatible with **IFS-based renderers** such as **JWildfire**, **Apophysis**, or any custom fractal software that uses 288-step gradients.

---

## 🔥 Features

### 🎚️ Gradient Stop Editor
- Click on the gradient bar to select a stop
- Add or remove stops with buttons
- Visual indicators show stop positions  
![Stop Editor]()

---

### 🖍️ Color Editing Panel
- Adjust selected stop's RGB values with sliders
- Preview color in real time  
![Color Sliders]("C:\Users\Prasad\Pictures\Screenshots\stops.png")

---

### 🎨 Color Wheel Picker
- Use the native color wheel to quickly choose any color
- Updates selected stop automatically  
![Color Picker]("C:\Users\Prasad\Pictures\Screenshots\colorw.png")

---

### 🧭 export .gradient files for IFS renderer
- Use the export Full .gradient to save it for IFS renderer
![export]("C:\Users\Prasad\Pictures\Screenshots\exp.png")
- saved
![export 2]("C:\Users\Prasad\Pictures\Screenshots\exp2.png")
---
### 🧭 export and import support
![supports]("C:\Users\Prasad\Pictures\Screenshots\sup.png")
-PNG and CSS SUPPORT
![supports]("C:\Users\Prasad\Pictures\Screenshots\sup2.png")

### 💾 Save / Load
- Save gradients as `.gradient` files compatible with **JWildfire**
- Load any existing `.gradient` file back into the editor  
![Save Dialog]("C:\Users\Prasad\Pictures\Screenshots\load.png")
- loading in iFS RENDERER
![Save Dialog]("C:\Users\Prasad\Pictures\Screenshots\load2.png")
![Save Dialog]("C:\Users\Prasad\Pictures\Screenshots\load3.png")
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
