# Install Tesseract OCR for Image Support

To enable PNG and JPG image text extraction, you need to install Tesseract OCR.

## macOS (using Homebrew)

```bash
# Install Tesseract OCR
brew install tesseract

# Optional: Install Thai language support for better Thai text recognition
brew install tesseract-lang
```

## Verify Installation

After installing, verify it works:

```bash
tesseract --version
```

You should see output like:
```
tesseract 5.x.x
```

## Test Image OCR

Once installed, you can upload PNG or JPG images to the app and they will automatically extract text using OCR.

## Supported Image Formats

- PNG (.png)
- JPEG/JPG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)
- TIFF (.tiff)
- WebP (.webp)

## Notes

- OCR works best with clear, high-contrast images
- Text should be clearly visible and not too small
- For Thai text, install `tesseract-lang` for better recognition
- The app will automatically use English + Thai if available, or fall back to English only

