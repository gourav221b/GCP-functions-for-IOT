

# GCP Cloud-to-Device IoT Controller 💡

This project demonstrates a modern, cloud-to-device IoT pipeline on Google Cloud Platform. It allows a user to control the onboard LED of a Raspberry Pi Pico W by clicking buttons on a simple web page.

The entire communication flow is handled in real-time using a serverless architecture built on **GCP Cloud Functions** and **Pub/Sub**, which is the recommended approach following the deprecation of Cloud IoT Core.

-----

## 🛠️ Tech Stack

  * **Cloud Platform:** Google Cloud Platform (GCP)
      * **Backend Logic:** Cloud Functions (2nd Gen)
      * **Messaging:** Cloud Pub/Sub
      * **Security:** Identity and Access Management (IAM)
  * **Hardware:** Raspberry Pi Pico W
  * **Device Firmware:** MicroPython
  * **Frontend:** HTML, CSS, and vanilla JavaScript

-----

## 🏗️ Architecture Flow

The command-and-control pipeline works as follows:

1.  **Frontend**: A user clicks a button on the `index.html` page. JavaScript sends an HTTP POST request to a public URL.
2.  **Cloud Function**: An HTTP-triggered Cloud Function receives the request, validates it, and publishes the command as a message to a Pub/Sub topic.
3.  **Pub/Sub Topic**: The `device-commands` topic receives the message from the Cloud Function.
4.  **Pub/Sub Subscription**: The `pico-command-subscription` is attached to the topic, holding the message in a queue for the device.
5.  **IoT Device**: The Raspberry Pi Pico W is connected to GCP's MQTT bridge and subscribed to its subscription. It receives the message and toggles its onboard LED.

-----

## 📋 Prerequisites

Before you begin, ensure you have the following:

  * A **Google Cloud Platform Account** with billing enabled.
  * The **`gcloud` CLI** installed and authenticated.
  * A **Raspberry Pi Pico W** microcontroller.
  * **Thonny IDE** installed for flashing MicroPython and uploading files to the Pico.
  * Your GCP Project ID handy.

-----

## 🚀 Setup and Deployment

Follow these steps to get the project running.

### 1\. Configure Your GCP Environment

First, set up the necessary services and permissions in your GCP project. Run these commands in your terminal.

```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable pubsub.googleapis.com \
    cloudfunctions.googleapis.com \
    iam.googleapis.com \
    run.googleapis.com \
    cloudbuild.googleapis.com

# 1. Create a service account for the device
gcloud iam service-accounts create pico-device-sa --display-name="Pico Device Service Account"

# 2. Grant the service account the Pub/Sub Subscriber role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:pico-device-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.subscriber"

# 3. Create and download the key file for the device
gcloud iam service-accounts keys create gcp_key.json \
    --iam-account="pico-device-sa@YOUR_PROJECT_ID.iam.gserviceaccount.com"

# 4. Create the Pub/Sub topic
gcloud pubsub topics create device-commands

# 5. Create the Pub/Sub subscription
gcloud pubsub subscriptions create pico-command-subscription --topic=device-commands
```

**Note:** A `gcp_key.json` file will be created in your current directory. This file is a secret and should be handled securely.

### 2\. Deploy the Cloud Function

This function acts as the bridge between your web frontend and Pub/Sub.

```bash
# Navigate to the cloud function directory
cd cloud-function/

# Deploy the function (this can take a few minutes)
gcloud functions deploy sendCommandToPubSub \
    --gen2 \
    --runtime=python311 \
    --region=us-central1 \
    --source=. \
    --entry-point=send_command \
    --trigger-http \
    --allow-unauthenticated

# After deployment, copy the trigger URL from the output.
# It will look like: https://your-region-your-project-id.cloudfunctions.net/sendCommandToPubSub
```

### 3\. Configure the Web Frontend

Point the web page to your newly deployed Cloud Function.

1.  Open the `frontend/index.html` file.
2.  Find the `API_ENDPOINT` constant in the `<script>` section.
3.  Replace the placeholder URL with the **trigger URL** you copied from the previous step.

### 4\. Program the IoT Device

Finally, flash the code onto your Raspberry Pi Pico W.

1.  **Move the Key File:** Copy the `gcp_key.json` file you generated in Step 1 into the `pico-w-micropython/` directory.
2.  **Edit Configuration:** Open `pico-w-micropython/main.py` and update the following variables:
      * `WIFI_SSID`: Your Wi-Fi network name.
      * `WIFI_PASS`: Your Wi-Fi password.
      * `GCP_PROJECT_ID`: Your GCP project ID.
3.  **Upload to Pico:**
      * Connect your Pico W to your computer.
      * Open Thonny and connect to the device.
      * Upload the following three files from the `pico-w-micropython/` directory to the root of your Pico:
          * `main.py`
          * `ujwt.py`
          * `gcp_key.json`
4.  **Run the Code:** In Thonny, press `Ctrl+D` to reboot the Pico and run the `main.py` script. Watch the shell for connection status messages.

-----

## ✨ How to Use

1.  Ensure your Pico W is running and has successfully connected to GCP (check the Thonny shell output).
2.  Open the `frontend/index.html` file in a web browser.
3.  Click the **"Turn LED ON"** and **"Turn LED OFF"** buttons.
4.  Watch the onboard LED on your Pico respond instantly\!

-----

## 🔒 Security Note

The `gcp_key.json` file contains private credentials and grants access to your GCP project.

  * **DO NOT** commit this file to a public Git repository.
  * The repository includes a `.gitignore` file to help prevent this automatically.
  * For production scenarios, explore more secure key management and distribution methods.