import os
from PIL import Image
from torchvision import transforms

# ====== 原始與輸出資料夾 ======
input_dir = "dataset"
output_dir = "augmented_dataset"
os.makedirs(output_dir, exist_ok=True)

# ====== PyTorch Augmentation Pipeline ======
transform = transforms.Compose([
    transforms.RandomHorizontalFlip(p=0.5),  
    transforms.RandomRotation(30),           
    # transforms.ColorJitter(
    #     brightness=0.2,
    #     contrast=0.2,
    #     saturation=0.2,
    #     hue=0.02
    # ),
    transforms.Resize((224, 224))  
])

# ====== Convert back to PIL to save ======
to_pil = transforms.ToPILImage()


# ====== 主程式 ======
for class_name in os.listdir(input_dir):
    class_path = os.path.join(input_dir, class_name)
    if not os.path.isdir(class_path):
        continue

    # 建立輸出子資料夾
    output_class_path = os.path.join(output_dir, class_name)
    os.makedirs(output_class_path, exist_ok=True)

    print(f"Processing class: {class_name}")

    for img_name in os.listdir(class_path):
        img_path = os.path.join(class_path, img_name)

        try:
            img = Image.open(img_path).convert("RGB")
        except:
            print(f"Skip invalid image: {img_path}")
            continue

        # ====== 每張圖做多次 augmentation ======
        
        aug_img = transform(img)

        new_filename = f"{os.path.splitext(img_name)[0]}.jpg"
        save_path = os.path.join(output_class_path, new_filename)
        aug_img.save(save_path)

print("PyTorch Data Augmentation finished!")
