# 🖼️ ImageType

Easy image editing for everyone: ImageType empowers visually impaired users to effortlessly add custom text to images for social media, greeting cards, and more, all with full screen reader compatibility. 🌟

---

## 🧐 Overview

**ImageType** is a professional desktop application designed to empower visually impaired and blind users to easily add custom text to images or create new graphics from scratch. 🚀 It focuses heavily on **strict accessibility standards** and provides a straightforward, high-contrast interface fully compatible with screen readers. 🎧 Whether you want to prepare text for social media posts, YouTube Shorts, or any other visual content, ImageType makes styling and positioning your words seamless.

---

## ✨ Core Features

- 📱 **Accessible Interface:** Built with PySide6 for absolute native compatibility with modern screen readers and accessibility tools.
- 🌍 **Multilingual Text Input:** Full support for typing in any language, with seamless rendering of **Right-to-Left (RTL) Arabic text** and mixed Arabic/English prose.
- 🔠 **Smart Font Fallback Engine:** Automatically detects if a system font lacks Arabic support and dynamically falls back to the embedded **Amiri** font to prevent text corruption or broken characters.
- ⚡ **Binary Search Sizing Optimization:** Implements an advanced binary search algorithm to automatically and instantly calculate the maximum perfect font size to fit your text within image boundaries when the **"Fit to Width"** checkbox is enabled.
- 🎯 **Precise Text Positioning:** Predefined layout anchoring grid (Top Left, Center, Bottom Right, etc.) that deactivates automatically when layout wrapping takes priority.
- 🎨 **Text Shadows & Outlines:** Optional drop shadows for high-contrast visibility against complex backgrounds, with automatic adaptive text outlining (stroke width) based on font color.
- 🖼️ **Flexible Background Systems:** Support for loading existing local images, generating solid color canvases, or exporting transparent PNG overlays.
- 📐 **Standard Aspect Ratios:** Quick presets for major digital formats including Standard (16:9), Square (1:1), and Portrait (9:16) for YouTube Shorts and Instagram Reels.
- 📋 **Direct Clipboard Export:** Features a one-click **"Copy to Clipboard"** button to paste your generated graphics straight into messaging or editing apps without saving files.
- 💾 **Local Profile & Preset Saving:** Save all your text styles, font configurations, colors, and canvas settings into custom template profiles for instant reuse later.
- 🎨 **Dynamic QSS Themes:** Full configuration for multiple application themes (like Dark Theme) that update the UI look on the fly without restarting.
- 🔄 **Embedded Automated Update Manager:** Built-in asynchronous network checker that checks GitHub releases to alert, download, and launch software installers safely.

---

## ⬇️ Download & Run

Go to the **[📥 Latest Releases Page](https://github.com/ahmedthebest31/ImageType/releases/latest)** to download the version that suits your needs:

### 1. ⚙️ Installed Version (Recommended)
- 💾 Download the official Windows `ImageType_Setup.exe` installer.
- 🛠️ Run the installer to register the program safely on your system environment.
- 📂 In this mode, all your editable assets (languages, templates, fonts, themes) are stored and safely managed under your user documents folder: `Documents/Ahmed Samy/ImageType/`.

### 2. 🧳 Portable Version
- 📦 Download the portable compressed archive file.
- 📂 Extract the directory anywhere on your computer or USB drive.
- 📁 To use your custom assets in portable mode, ensure your asset folders are placed inside a folder named `data` right next to the main `ImageType.exe` file.

---

## 🛠️ For Developers (Local Setup)

This project uses **uv** for blazing-fast, reliable Python dependency and virtual environment management. ⚡

1. 👥 Clone the repository: `git clone https://github.com/ahmedthebest31/ImageType.git`
2. 📂 Navigate to the project directory: `cd ImageType`
3. 🔄 Install dependencies and sync the virtual environment: `uv sync`
4. 🚀 Run the application in development mode: `uv run main.py`
5. 🏗️ Build the standalone production executable using PyInstaller: `uv run pyinstaller --noconfirm --onefile --windowed --name="ImageType" --icon="assets/icon_64.ico" main.py`

---

## 💡 Creative Applications & Ideas

- ✉️ **Social Media Greetings:** Easily design personalized holiday greeting cards or event announcements for platforms like Facebook and X.
- 🎬 **Video Thumbnails & Overlays:** Produce rapid thumbnail text overlays or descriptive frames for YouTube Shorts, TikToks, and Instagram Reels.
- 📚 **Educational Graphics:** Generate clear images with text for slide presentations, tutorials, or study notes to make information visually scannable.
- 💬 **Inspirational Quote Graphics:** Instantly turn your favorite written quotes or text snippets into beautifully styled shareable graphics.

---

## ⚖️ License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the [LICENSE](LICENSE) file for more details.

---

## 🤝 Contributions & Suggestions

Your feedback is highly valued! If you have ideas for new layout features, encounter bugs, or want to contribute code:
- 🐛 **Open an Issue:** Describe any bugs you find or suggest new feature requests.
- 🔧 **Open a Pull Request:** Submit improvements or new UI translation blocks directly to the project.

---

## 📞 Contact

For any questions, business tracking, or technical support, feel free to open an official issue directly on GitHub.