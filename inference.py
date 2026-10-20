import numpy as np
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    import tensorflow.lite as tflite

class DeepfakeDetector:
    def __init__(self, model_path="veritrust_audio.tflite"):
        self.interpreter = tflite.Interpreter(model_path=model_path)
        self.interpreter.allocate_tensors()

        # Get input and output tensor details
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

    def predict(self, feature_matrix):
        """
        Runs inference on normalized audio features.
        Returns: spoof_score (float between 0.0 and 1.0)
        """
        if feature_matrix is None:
            return 0.5  # Neutral fallback

        target_shape = self.input_details[0]['shape']
        
        # Reshape input matrix to match TFLite expected shape: [Batch, Height, Width, Channels]
        input_data = np.expand_dims(feature_matrix, axis=0)
        
        if len(input_data.shape) == 3:
            input_data = np.expand_dims(input_data, axis=-1)

        # Pad or slice to match target shape dynamically
        padded_input = np.zeros(target_shape, dtype=np.float32)
        h = min(input_data.shape[1], target_shape[1])
        w = min(input_data.shape[2], target_shape[2])
        padded_input[0, :h, :w, 0] = input_data[0, :h, :w, 0]

        # Feed input to TFLite
        self.interpreter.set_tensor(self.input_details[0]['index'], padded_input)
        self.interpreter.invoke()

        # Retrieve prediction score (0.0 = Real/Bonafide, 1.0 = Spoof/Deepfake)
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        spoof_probability = float(output_data[0][0])

        return spoof_probability

