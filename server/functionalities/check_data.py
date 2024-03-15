import torch
import matplotlib.pyplot as plt
import torch.nn as nn
import torchvision
from numpy import transpose
from image_recognition import Net, testloader, classes
from os.path import join

cwd: str = '/'.join(__file__.split("/")[:-2])

# Load the model
PATH = join(cwd, 'models', 'cifar_net.pth')
net = Net()
net.load_state_dict(torch.load(PATH))

# Overall test
correct: int = 0
total: int = 0
with torch.no_grad():
    for data in testloader:
        images, labels = data
        outputs = net(images)
        _, predicted = torch.max(outputs.data, 1)
        total += labels.size(0)
        correct += (predicted == labels).sum().item()

print(f'Accuracy of the network on the 10 000 test images: {100 * correct // total} %')

correct_pred = {classname: 0 for classname in classes}
total_pred = {classname: 0 for classname in classes}

with torch.no_grad():
    for data in testloader:
        images, labels = data
        outputs = net(images)
        _, predictions = torch.max(outputs, 1)
        for label, prediction in zip(labels, predictions):
            if label == prediction:
                correct_pred[classes[label]] += 1
            total_pred[classes[label]] += 1

for classname, correct_count in correct_pred.items():
    accuracy = 100 * float(correct_count) / total_pred[classname]
    print(f'Accuracy for class: {classname:5s} is {accuracy:.1f} %')

# Sample test
def imshow(img):
    img = img / 2 + 0.5
    npimg = img.numpy()
    plt.imshow(transpose(npimg, (1, 2, 0)))
    plt.show()

dataiter = iter(testloader)
images, labels = next(dataiter)

print(f'{'GroundTruth:':15s} ', ' '.join(f'{classes[labels[j]]:5s}' for j in range(4)))

outputs = net(images)
_, predicted = torch.max(outputs, 1)
print(f'{'Predicted:':15s} ', ' '.join(f'{classes[predicted[j]]:5s}' for j in range(4)))

imshow(torchvision.utils.make_grid(images))