import arabic_reshaper
from PIL import ImageFont
import os

font_path = "C:/Windows/Fonts/arial.ttf"  # usually has arabic
font_path2 = "C:/Windows/Fonts/comic.ttf" # might not have all?
amiri = os.path.join("fonts", "Amiri", "Amiri-Regular.ttf")

text = "مرحبا" # arabic hello
reshaped_text = arabic_reshaper.reshape(text)

def check_font(fp, txt):
    try:
        font = ImageFont.truetype(fp, 20)
        tofu_box = font.getmask('\uFFFF').getbbox()
        tofu_box2 = font.getmask('\u0000').getbbox()
        
        for char in set(txt): # checking the reshaped text
            if char.isspace(): continue
            cb = font.getmask(char).getbbox()
            if cb == tofu_box or cb == tofu_box2 or cb is None:
                return False
        return True
    except Exception as e:
        print(e)
        return False

print("Arial:", check_font(font_path, reshaped_text))
print("Comic:", check_font(font_path2, reshaped_text))
if os.path.exists(amiri):
    print("Amiri:", check_font(amiri, reshaped_text))
