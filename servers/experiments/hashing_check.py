from PIL import Image, ImageDraw, ImageFont
import imagehash

def spell_hash(text, font_path="servers\\experiments\\unifont-15.1.04.otf", font_size=50):
    """
    Convert text to an image and return the image hash, automatically computing image size based on text.
    
    Args:
    text (str): The Unicode text to convert into an image.
    font_path (str): Optional. Path to a .ttf font file. Uses default font if None.
    font_size (int): Font size.
    
    Returns:
    str: A hexadecimal string representing the image's hash.
    """
    # Load a font. Use a default PIL font if font_path is not provided.
    if font_path:
        font = ImageFont.truetype(font_path, font_size)
    else:
        # Fallback to a default font if no path is provided
        font = ImageFont.load_default()
    
    # Create a dummy image to calculate text dimensions accurately
    dummy_img = Image.new('RGB', (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    
    # Draw the text on the dummy image to calculate its bounding box
    dummy_draw.text((0, 0), text, font=font, fill=(0, 0, 0))
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    
    # Calculate text width and height from the bounding box
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    
    # Create an actual image with a white background, dynamically sized
    img = Image.new('RGB', (text_width + 20, text_height + 20), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Draw the text on the actual image, centered
    d.text((10, 10), text, fill=(0, 0, 0), font=font)
    # Compute image hash using imagehash library
    hash_value = imagehash.average_hash(img)
    
    # Return the hash as a hexadecimal string
    return hash_value

path = "servers\\experiments\\unifont-15.1.04.otf"


# Example usage:
if __name__ == "__main__":
    namaste = text_to_image_hash("नमस्ते", font_path=path)
    wrong1 = text_to_image_hash("नमस्तै", font_path=path)
    wrong2 = text_to_image_hash("नमस्तेय", font_path=path)
    paanee = text_to_image_hash("पानी", font_path=path)

    print("result: ", namaste-wrong1)
    # returns 1
    print("result: ", namaste-wrong2)
    # returns 7
    print("result: ", namaste-paanee)
    # returns 15

