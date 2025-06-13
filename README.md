# Orthodox Translation Assistant

Orthodox Translation Assistant is a web application designed to assist with the translation of texts from English to Traditional Chinese, with a special focus on Orthodox Christian theological content. It also provides functionality to identify and annotate Bible quotes within a given text.

## Key Features

*   **Orthodox Christian Focused Translation**: Translates English text to Traditional Chinese, prioritizing accurate and contextually appropriate Orthodox Christian terminology and tone.
*   **Bible Quote Annotation**: Identifies and annotates biblical quotations within texts, providing standard references (e.g., John 1:2-5).
*   **OpenRouter API Integration**: Leverages various large language models via the OpenRouter API for its core functionalities.
*   **User-Friendly Interface**: Built with Streamlit to provide an intuitive and interactive web application.
*   **Arena Mode**: Allows side-by-side comparison of translations/annotations from two different AI models.
*   **Debug Mode**: Offers a view of the processed queries sent to the LLM, useful for understanding how special commands (`translate`, `annotate`) modify the input.
*   **Local API Key Storage**: Securely saves your OpenRouter API key locally for persistence between sessions.

## Setup and Usage

To run the Orthodox Translation Assistant locally, follow these steps:

1.  **Prerequisites**:
    *   Ensure you have Python 3.7+ installed on your system.

2.  **Clone the Repository (Optional)**:
    *   If you haven't already, clone this repository to your local machine.

3.  **Install Dependencies**:
    *   Navigate to the project's root directory in your terminal.
    *   Install the required Python packages using pip:
        ```bash
        pip install -r requirements.txt
        ```

4.  **Set Up OpenRouter API Key**:
    *   This application requires an API key from [OpenRouter.ai](https://openrouter.ai/keys).
    *   Once you have your key, you can enter it directly into the application's settings interface (found in the sidebar). The key will be saved locally for future sessions.

5.  **Run the Application**:
    *   In your terminal, from the project's root directory, execute the following command:
        ```bash
        streamlit run app.py
        ```
    *   This will start the Streamlit development server, and the application should open in your default web browser.

## Available Commands

The application supports special commands that can be typed into the chat input:

*   **`translate [text]`**: Use this command to translate the provided `[text]` from English to Traditional Chinese. If "Orthodox Translation Mode" is enabled in the settings, the translation will use specialized Orthodox Christian theological context.
*   **`annotate [text]`**: Use this command to analyze the provided `[text]` for any potential Bible quotes. If found, the quotes will be annotated with their respective biblical references.

## Deployment

This application includes a `railway.json` file, configuring it for deployment on the [Railway](https://railway.app/) platform using Nixpacks.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page if you want to contribute.
