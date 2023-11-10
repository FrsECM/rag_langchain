import argparse
import fitz
import os
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument('--src_dir',default="data/pdf")
parser.add_argument('--dst_dir',default="data/txt")


def pdf_to_text(src_dir:str,dst_dir:str):
    assert os.path.exists(src_dir),"Source directory should exist"
    os.makedirs(dst_dir,exist_ok=True)
    pdf_filepaths = [os.path.join(src_dir,f) for f in os.listdir(src_dir) if f.endswith('.pdf')]
    for pdf_filepath in pdf_filepaths:
        doc = fitz.open(pdf_filepath)
        pdf_name = os.path.basename(pdf_filepath)
        with open(os.path.join(dst_dir,pdf_name+".txt"),'w') as dst_file:
            for page in tqdm(doc,desc=pdf_name):
                text = page.get_text()
                dst_file.write(text)

if __name__ == "__main__":
    args = parser.parse_args()
    pdf_to_text(**vars(args))