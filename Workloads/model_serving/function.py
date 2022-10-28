import logging
import time

import torch
import torchvision.models.alexnet
from PIL import Image
from torchvision import transforms

logging.basicConfig(level=logging.INFO)


def func():
    model = torchvision.models.resnet50(pretrained=False)
    model.load_state_dict(torch.load('resnet.pth'))
    model.eval()

    input_image = Image.open('cat.jpg')
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    input_tensor = preprocess(input_image)
    # create a mini-batch as expected by the model
    input_batch = input_tensor.unsqueeze(0)

    with torch.no_grad():
        output = model(input_batch)
    # Tensor of shape 1000, with confidence scores over Imagenet's 1000 classes
    # The output has unnormalized scores. To get probabilities, you can run a softmax on it.
    probabilities = torch.nn.functional.softmax(output[0], dim=0)

    # Read the categories
    with open("imagenet_classes.txt", "r") as f:
        categories = [s.strip() for s in f.readlines()]
    # Show top categories per image
    # top5_prob, top5_catid = torch.topk(probabilities, 5)
    # for i in range(top5_prob.size(0)):
    #     print(categories[top5_catid[i]], top5_prob[i].item())


if __name__ == '__main__':
    start_t = time.perf_counter()

    func()

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
