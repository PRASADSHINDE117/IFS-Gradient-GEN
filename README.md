# IFS-Gradient-GEN
A desktop app for creating, editing, and exporting .gradient files compatible with IFS-based renderers like JWildfire. Features include a visual gradient editor, color wheel, RGB sliders, and one-click export to a 288-step compatible format.

## ⬇️ Download

You can download the latest version of the standalone app for Windows here:

🔗 [Download Gradient Editor (.exe)](https://github.com/PRASADSHINDE117/IFS-Gradient-GEN/releases/latest)

# IFS Gradient Editor 🎨
<img width="1204" height="706" alt="gui" src="https://github.com/user-attachments/assets/101e7823-61e8-4618-93a4-ed605a4f52a9" />
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
<img width="1203" height="741" alt="stops" src="https://github.com/user-attachments/assets/681357e5-7df1-4153-8fdd-24aea589264a" />
---

### 🎨 Color Wheel Picker
- Use the native color wheel to quickly choose any color
- Updates selected stop automatically  
<img width="1364" height="805" alt="colorw" src="https://github.com/user-attachments/assets/2fd844ea-8517-4267-b33b-2a0576158958" />


---

### 🧭 export .gradient files for IFS renderer
- Use the export Full .gradient to save it for IFS renderer
<img width="1197" height="713" alt="exp" src="https://github.com/user-attachments/assets/f26a72ee-01be-4fdf-a948-4dce748386cd" />

- saved
<img width="516" height="144" alt="exp (2)" src="https://github.com/user-attachments/assets/7b63ad2d-1a3c-4d45-87fc-b4ec2a92fbe3" />

---
### 🧭 export and import support
<img width="1039" height="87" alt="sup" src="https://github.com/user-attachments/assets/fe787341-3af0-4790-922f-b2522017cbe3" />
- PNG and CSS SUPPORT
<img width="362" height="148" alt="sup2" src="https://github.com/user-attachments/assets/d5238dcb-f966-465a-b044-a8bea88c7fab" />


### 💾 Save / Load
- Save gradients as `.gradient` files compatible with **JWildfire**
- Load any existing `.gradient` file back into the editor  
<img width="1165" height="664" alt="load" src="https://github.com/user-attachments/assets/07da2674-a923-4b7f-8bba-9405cf68d772" />

- loading in iFS RENDERER
<img width="1902" height="983" alt="load2" src="https://github.com/user-attachments/assets/570c31e1-0775-4d4b-bcb5-56fd9c02d2a1" />
<img width="1919" height="1020" alt="load3" src="https://github.com/user-attachments/assets/66e39497-967f-41ce-8539-7d306f9739da" />
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
