import cv2
from fuzzywuzzy import fuzz
import streamlit as st
from ultralytics import YOLO
import tempfile
import numpy as np
from tensorflow.keras.models import model_from_json
import easyocr


# Paths to models
logo_detection_model_path = "./model/angelhack_yolov9.pt"
face_classifier_path = "./model/haarcascade_frontalface_default.xml"
model_json_file = "./model/model.json"
model_weights_file = "./model/Latest_Model.h5"
human_detection_model_path = "./model/Human_detection.pt"

# Streamlit page configuration
st.set_page_config(
    page_title="Object Detection using YOLOv9",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.header("Video Detection")

    option = st.selectbox(
        "Choose detection type:",
        ("Logo detect", "Emotion detect", "Human", "OCR"),
        placeholder="Select detection type..."
    )
    source_vid = st.file_uploader("Choose a file", type=["jpeg", "jpg", "png", "webp", "mp4"])

if option == "Logo detect" and source_vid is not None:
    try:
        model = YOLO(logo_detection_model_path)
        st.success("Model loaded successfully!")
    except Exception as ex:
        st.error(f"Unable to load model. Check the specified path: {logo_detection_model_path}")
        st.error(ex)

    if st.sidebar.button('Logo Detect'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(source_vid.read())
            temp_filename = temp_file.name

            vid_cap = cv2.VideoCapture(temp_filename)
            st_frame = st.empty()
            while vid_cap.isOpened():
                success, image = vid_cap.read()
                if success:
                    image = cv2.resize(image, (720, int(720 * (9 / 16))))
                    res = model.predict(image, conf=0.1)
                    result_tensor = res[0].boxes
                    res_plotted = res[0].plot()
                    st_frame.image(res_plotted, caption='Detected Video', channels="BGR", use_column_width=True)
                else:
                    vid_cap.release()
                    break

elif option == "Emotion detect" and source_vid is not None:
    try:
        face_classifier = cv2.CascadeClassifier(face_classifier_path)
        with open(model_json_file, "r") as json_file:
            loaded_model_json = json_file.read()
            classifier = model_from_json(loaded_model_json)
            classifier.load_weights(model_weights_file)
        st.success("Emotion detection model loaded successfully!")
    except Exception as ex:
        st.error(f"Unable to load model or classifier. Check the specified paths.")
        st.error(ex)

    if st.sidebar.button('Emotion Detect'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(source_vid.read())
            temp_filename = temp_file.name

            image = cv2.imread(temp_filename)
            if image is not None:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                faces = face_classifier.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    fc = gray[y:y+h, x:x+w]
                    roi = cv2.resize(fc, (48, 48))
                    roi = roi[np.newaxis, :, :, np.newaxis]  # Add batch and channel dimensions
                    pred = classifier.predict(roi)
                    text_idx = np.argmax(pred)
                    text_list = ['Angry', 'Disgust', 'Fear', 'Happy', 'Neutral', 'Sad', 'Surprise']
                    text = text_list[text_idx]

                    cv2.putText(image, text, (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 255), 2)
                    cv2.rectangle(image, (x, y), (x+w, y+h), (0, 0, 255), 2)

                st.image(image, caption='Detected Emotions', channels="BGR", use_column_width=True)
            else:
                st.error("Error: Unable to read the uploaded image.")

elif option == "Human" and source_vid is not None:
    try:
        model = YOLO(human_detection_model_path)
        st.success("Model loaded successfully!")
    except Exception as ex:
        st.error(f"Unable to load model. Check the specified path: {logo_detection_model_path}")
        st.error(ex)

    if st.sidebar.button('Logo Detect'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(source_vid.read())
            temp_filename = temp_file.name

            vid_cap = cv2.VideoCapture(temp_filename)
            st_frame = st.empty()
            while vid_cap.isOpened():
                success, image = vid_cap.read()
                if success:
                    image = cv2.resize(image, (720, int(1080 * (9 / 16))))
                    res = model.predict(image, conf=0.3)
                    result_tensor = res[0].boxes
                    res_plotted = res[0].plot()
                    st_frame.image(res_plotted, caption='Detected Video', channels="BGR", use_column_width=True)
                    st.write(f"Total number of humans detected: **{len(result_tensor)}**")
                else:
                    vid_cap.release()
                    break

elif option == "OCR" and source_vid is not None:
    strong_list = ["Tiger", "Heineken", "BiaViet", "Strongbow", "Larue", "Bivina", "Edelweiss"]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(source_vid.read())
        temp_filename = temp_file.name

    image = cv2.imread(temp_filename)

    if image is not None:
        reader = easyocr.Reader(['ch_sim', 'en'])
        result = reader.readtext(image)

        if st.sidebar.button('Extract Text'):

            max_score = 0.0
            best_match = ""
            detected_text = ""

            for text in result:
                current_text = text[1]

                for item in strong_list:
                    similarity_score = fuzz.ratio(current_text.lower(), item.lower())
                    if similarity_score > max_score:
                        max_score = similarity_score
                        best_match = item
                        detected_text = current_text

            for text in result:
                if text[1] == detected_text:
                    bbox = text[0]
                    cv2.rectangle(image, (bbox[0][0], bbox[0][1]), (bbox[2][0], bbox[2][1]), (255, 0, 0), 2)
                    break

            st.image(image, caption='Detected Text with Highest Score', channels="BGR", use_column_width=True)

    else:
        st.error("Error: Unable to read the uploaded image.")
