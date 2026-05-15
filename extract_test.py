from pypdf import PdfReader

reader = PdfReader(r"D:\SynologyDrive\SynologyDrive\wzq\Language\CET\CET project\CET-4 真题\cet4_2024\cet4_2024_06_1.pdf")
text = ""
for page in reader.pages:
    text += page.extract_text() + "\n"

# Print first 3000 chars
print(text[:3000])
print("\n\n===== MIDDLE =====")
print(text[3000:6000])
print("\n\n===== END =====")
print(text[-2000:])
