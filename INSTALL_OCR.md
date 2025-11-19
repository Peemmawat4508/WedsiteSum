# Installing Tesseract OCR for Image Text Extraction

To enable OCR (Optical Character Recognition) for images, you need to install Tesseract OCR on your system.

## macOS

```bash
brew install tesseract
brew install tesseract-lang  # For Thai language support (optional but recommended)
```

## Linux (Ubuntu/Debian)

```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
sudo apt-get install tesseract-ocr-tha  # For Thai language support (optional)
```

## Windows

1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer
3. Add Tesseract to your system PATH

## Verify Installation

After installing, verify it works:

```bash
tesseract --version
```

## Note

- Image OCR will work automatically once Tesseract is installed
- The system will try to use English + Thai language models if available
- Falls back to English-only if Thai models are not installed
- OCR works best with clear, high-contrast images

