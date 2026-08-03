import logging
from pathlib import Path

import cv2
import numpy as np

from processing.exceptions import ImagePreprocessingException

logger = logging.getLogger("processing")


class ImagePreprocessor:
    """
    Preprocesses images for OCR.

    Uses a lightweight pipeline matching the test file's approach:
    grayscale conversion + light Gaussian blur.
    """

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

        blurred_image = self._gaussian_blur(
            image=grayscale_image,
        )

        return self._save_image(
            image=blurred_image,
            output_path=image_path,
        )

    def preprocess_array(
        self,
        image_rgb: np.ndarray,
    ) -> np.ndarray:
        """
        Preprocess an in-memory RGB image for OCR.

        Args:
            image_rgb: RGB numpy array.

        Returns:
            Preprocessed grayscale numpy array.
        """

        gray = self._convert_to_grayscale(image=image_rgb)
        return self._gaussian_blur(image=gray)

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
            image: Input image (BGR or RGB).

        Returns:
            Grayscale image.

        Raises:
            ImagePreprocessingException:
                If grayscale conversion fails.
        """

        # If already grayscale, return as-is
        if len(image.shape) == 2:
            return image

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

    def _gaussian_blur(
        self,
        image: np.ndarray,
    ) -> np.ndarray:
        """
        Apply a light Gaussian blur to reduce noise.

        Uses a (3, 3) kernel matching the test file's approach.

        Args:
            image: Grayscale image.

        Returns:
            Blurred image.
        """

        return cv2.GaussianBlur(image, (3, 3), 0)

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