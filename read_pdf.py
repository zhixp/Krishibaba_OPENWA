import PyPDF2

pdf_path = "KISAN_CONVO.pdf"
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    print(f"Total pages: {len(reader.pages)}\n")
    print("=" * 80)
    
    for i, page in enumerate(reader.pages):
        print(f"\n--- Page {i+1} ---\n")
        text = page.extract_text()
        print(text)
        print("\n" + "=" * 80)
