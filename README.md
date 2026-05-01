\# AI-Based Cell Nuclei Segmentation and Counting in Microscopy Images



\## Project Overview

This project presents an AI-based microscopy image analysis system for nuclei segmentation and counting in histopathology images.  

The system uses a U-Net-based segmentation pipeline and postprocessing to generate predicted nuclei masks, estimate nuclei counts, visualize density distribution, and extract morphology features.



The project was developed as part of:



\*\*ENS 005 – Application of AI in Image Processing\*\*



\---



\## Main Features

\- Nuclei segmentation using a U-Net model

\- Nuclei counting using connected-components postprocessing

\- Corrected evaluation using XML-based ground-truth nucleus counts

\- Density heatmap generation

\- Morphology feature extraction

\- Overlay visualization

\- CSV export of results

\- HTML dashboard prototype

\- Streamlit interactive prototype



\---



\## Dataset

The project uses microscopy images and XML annotations derived from the \*\*MoNuSeg\*\* dataset.



\### Preprocessing

The preprocessing pipeline includes:

\- reading XML annotation files

\- converting annotations into binary masks

\- matching images and masks

\- splitting data into train / validation / test

\- building PyTorch dataset loaders



\---



\## Project Structure

```text

project/

│

├── src/

│   ├── app.py

│   ├── generate\_density\_maps.py

│   ├── extract\_morphology.py

│   ├── make\_report4\_dashboard.py

│

├── data/

│   └── splits/

│       └── all.csv

│

├── outputs/

│   ├── counting\_batch\_refined\_xmlgt/

│   ├── density\_maps/

│   ├── morphology/

│   └── report4\_evidence/

│

├── requirements.txt

├── README.md

