import logging
from pathlib import Path

logger = logging.getLogger("processing")
import numpy as np
import cv2

from processing.exceptions import ImagePreprocessingException

class ImagePreprocessor:

    def preprocess(
        self,
        image_path: Path,
    ) -> Path:
        """
        Preprocess an image for OCR.

        Args:
            image_path: Path to the image to preprocess.

        Returns:
            Path to the preprocessed image.

        Raises:
            ImagePreprocessingException:
                If preprocessing fails.
        """

        logger.debug("Preprocessing image: %s", image_path.name)
        image = self._load_image(
            image_path=image_path,
        )

        grayscale_image = self._convert_to_grayscale(
            image=image,
        )

        denoised_image = self._denoise(
            image=grayscale_image,
        )

        thresholded_image = self._threshold(
            image=denoised_image,
        )

        # Calculating the text density
        text_density = self._calculate_text_density(thresholded_image)
        logger.debug("Image text density: %.4f", text_density)

        # If text is extremely thin (e.g., less than 2% of the image), dilate to thicken it
        if text_density > 0 and text_density < 0.02:
            logger.debug("Text density too low, dilating image.")
            thresholded_image = self._dilate(image=thresholded_image)
        # If text is unusually thick (e.g., more than 10% of the image), erode to thin it
        elif text_density > 0.10:
            logger.debug("Text density too high, eroding image.")
            thresholded_image = self._erode(image=thresholded_image)

        return self._save_image(
            image=thresholded_image,
            output_path=image_path,
        )

    def _load_image(self, image_path: Path) -> np.ndarray:
        """
            Load an image from disk.

            Args:
                image_path: Path to the image.

            Returns:
                Loaded image.

            Raises:
                ImagePreprocessingException:
                    If the image cannot be loaded.
        """

        if not image_path.exists():
            logger.error("Image file not found: %s", image_path)
            raise ImagePreprocessingException(
                detail=f"Image '{image_path}' does not exist."
            )

        image = cv2.imread(str(image_path))

        if image is None:
            logger.error("cv2 failed to load image: %s", image_path)
            raise ImagePreprocessingException(
                detail=f"Failed to load image '{image_path}'."
            )

        return image

    def _convert_to_grayscale(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Convert an image to grayscale.

        Args:
            image: Input image.

        Returns:
            Grayscale image.

        Raises:
            ImagePreprocessingException:
                If grayscale conversion fails.
        """

        try:
            return cv2.cvtColor(
                image,
                cv2.COLOR_BGR2GRAY,
            )

        except cv2.error as exc:
            logger.error("cv2 failed to convert image to grayscale: %s", exc)
            raise ImagePreprocessingException(
                detail="Failed to convert image to grayscale."
            ) from exc

    def _threshold(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Apply adaptive thresholding to enhance text.

        Args:
            image: Grayscale image.

        Returns:
            Thresholded image.

        Raises:
            ImagePreprocessingException:
                If thresholding fails.
        """

        try:
            return cv2.adaptiveThreshold(
                src=image,
                maxValue=255,
                adaptiveMethod=cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                thresholdType=cv2.THRESH_BINARY,
                blockSize=11,
                C=2,
            )

        except cv2.error as exc:
            logger.error("cv2 failed to apply threshold: %s", exc)
            raise ImagePreprocessingException(
                detail="Failed to apply adaptive threshold."
            ) from exc

    def _save_image(
        self,
        image: np.ndarray,
        output_path: Path,
    ) -> Path:
        """
        Save the processed image.

        Args:
            image: Processed image.
            output_path: Destination path.

        Returns:
            Path to the saved image.

        Raises:
            ImagePreprocessingException:
                If the image cannot be saved.
        """

        try:
            success = cv2.imwrite(
                str(output_path),
                image,
            )

            if not success:
                logger.error("cv2 failed to write image: %s", output_path)
                raise ImagePreprocessingException(
                    detail=f"Failed to save image '{output_path}'."
                )

            return output_path

        except cv2.error as exc:
            logger.error("cv2 error saving image '%s': %s", output_path, exc)
            raise ImagePreprocessingException(
                detail=f"Failed to save image '{output_path}'."
            ) from exc
    
    def _denoise(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Remove noise from an image while preserving text edges.

        Args:
            image: Grayscale image.

        Returns:
            Denoised image.

        Raises:
            ImagePreprocessingException:
                If denoising fails.
        """

        try:
            return cv2.fastNlMeansDenoising(
                src=image,
                h=10,
                templateWindowSize=7,
                searchWindowSize=21,
            )

        except cv2.error as exc:
            logger.error("cv2 failed to denoise image: %s", exc)
            raise ImagePreprocessingException(
                detail="Failed to denoise image."
            ) from exc
    
    def _dilate(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        kernel = np.ones((2, 2), np.uint8)

        return cv2.dilate(
            image,
            kernel,
            iterations=1,
        )
    
    def _erode(
        self,
        image: np.ndarray,
    ) -> np.ndarray:

        kernel = np.ones((2, 2), np.uint8)

        return cv2.erode(
            image,
            kernel,
            iterations=1,
        )
    
    def _calculate_text_density(
        self,
        image: np.ndarray,
    ) -> float:
        total_pixels = image.size
        text_pixels = total_pixels - cv2.countNonZero(image)

        return text_pixels / total_pixels