import sys
import os
import cv2
import numpy as np
from rembg import remove
from PIL import Image, ImageEnhance, ImageFilter

def detect_face(image_path):
    # Load the image in grayscale
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None:
        raise ValueError("Failed to load the image.")
    
    # Load the pre-trained face detector model
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Detect faces in the image
    faces = face_cascade.detectMultiScale(image, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))
    
    # Return the detected faces
    return faces

def enhance_image(image):
    # Enhance brightness
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)  # Increase brightness dynamically
    
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(1.3)  # Increase contrast dynamically
    
    # Enhance sharpness
    sharpness = estimate_sharpness(image)
    if sharpness < 30:
        enhancer = ImageEnhance.Sharpness(image)
        image = enhancer.enhance(1.5)  # Increase sharpness dynamically
    
    # Apply Gaussian blur for noise reduction
    image = image.filter(ImageFilter.GaussianBlur(radius=1))
    
    return image

def estimate_sharpness(image):
    # Calculate image sharpness
    array = np.array(image)
    sharpness = np.sqrt((array[:-1, :-1] - array[:-1, 1:]) ** 2 + (array[:-1, :-1] - array[1:, :-1]) ** 2).mean()
    return sharpness

def process_passport_photo(input_path, output_path, target_size=(3000, 3000), margin_ratio=0.6, background_color=(255, 255, 255)):
    try:
        # Remove background using Rembg
        with open(input_path, 'rb') as i:
            input_image = i.read()
            output_image = remove(input_image)

        # Save the intermediate result
        with open('temp_output.png', 'wb') as o:
            o.write(output_image)

        # Detect faces in the image
        faces = detect_face('temp_output.png')

        if len(faces) == 0:
            print("No faces detected.")
            return

        # Automatically select the largest face
        selected_face = max(faces, key=lambda face: face[2] * face[3])
        x, y, w, h = selected_face

        # Load the original image
        original_image = Image.open('temp_output.png')

        # Calculate dynamic margins
        image_width, image_height = original_image.size
        margin_x = int(w * margin_ratio)
        margin_y = int(h * margin_ratio)

        # Ensure there is enough space around the face
        if x - margin_x < 0:
            margin_x = x
        if y - margin_y < 0:
            margin_y = y
        if x + w + margin_x > image_width:
            margin_x = image_width - x - w
        if y + h + margin_y > image_height:
            margin_y = image_height - y - h

        # Adjust cropping area based on face size and position with dynamic margins
        crop_x = max(0, x - margin_x)
        crop_y = max(0, y - margin_y)
        crop_w = min(w + 2 * margin_x, image_width - crop_x)
        crop_h = min(h + 2 * margin_y, image_height - crop_y)

        # Create a background image
        background = Image.new('RGBA', original_image.size, (*background_color, 255))

        # Composite the original image onto the background
        combined_image = Image.alpha_composite(background, original_image.convert('RGBA'))

        # Crop the image to include the face and some margin
        passport_photo = combined_image.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))

        # Resize the cropped image to the desired target size
        resized_photo = passport_photo.resize(target_size, Image.LANCZOS)

        # Enhance the resized photo
        enhanced_photo = enhance_image(resized_photo)

        # Save the enhanced photo as the final passport photo
        enhanced_photo.convert('RGB').save(output_path)

        print("Passport photo generated successfully.")

    except Exception as e:
        print("Error occurred during processing:", e)
    finally:
        # Clean up temporary files
        if os.path.exists('temp_output.png'):
            os.remove('temp_output.png')

if __name__ == "__main__":
    input_path = sys.argv[1]
    output_path = sys.argv[2]  # Accept output path as a command line argument
    process_passport_photo(input_path, output_path)
