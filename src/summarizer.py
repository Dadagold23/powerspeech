"""
Text Summarization Module (summarizer.py)

Uses Hugging Face Transformers with BART (facebook/bart-large-cnn)
to produce abstractive summaries of transcribed text.

Objective 2: Implement a text summarization module using NLP techniques.

Author: [Your Name]
Date: 2026
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Load model config from environment
SUMMARIZATION_MODEL = os.getenv("SUMMARIZATION_MODEL", "facebook/bart-large-cnn")
SUMMARY_MAX_LENGTH = int(os.getenv("SUMMARY_MAX_LENGTH", 150))
SUMMARY_MIN_LENGTH = int(os.getenv("SUMMARY_MIN_LENGTH", 40))


class SummarizationModule:
    """
    Performs abstractive text summarization using a pre-trained
    Hugging Face Transformers pipeline (BART or T5).

    Attributes:
        model_name (str): Hugging Face model ID
        pipeline: Loaded summarization pipeline
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or SUMMARIZATION_MODEL
        self.pipeline = None
        logger.info(f"SummarizationModule initialized with model: '{self.model_name}'")

    def load_pipeline(self):
        """Load the model and tokenizer for summarization (lazy loading)."""
        if self.pipeline is None:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
            logger.info(f"Loading summarization model '{self.model_name}'...")
            tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)

            # Wrapper to emulate the legacy 'pipeline' function signature
            class PipelineWrapper:
                def __init__(self, m, t, model_name):
                    self.model = m
                    self.tokenizer = t
                    self.model_name = model_name

                def __call__(self, text, **kwargs):
                    prefix = "summarize: " if "t5" in self.model_name.lower() else ""
                    inputs = self.tokenizer(
                        prefix + text,
                        return_tensors="pt",
                        truncation=True,
                        max_length=1024
                    )
                    outputs = self.model.generate(
                        **inputs,
                        max_length=kwargs.get("max_length", 150),
                        min_length=kwargs.get("min_length", 40),
                        do_sample=kwargs.get("do_sample", False),
                        num_beams=4
                    )
                    summary_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
                    return [{"summary_text": summary_text}]

            self.pipeline = PipelineWrapper(model, tokenizer, self.model_name)
            logger.info("Summarization model and tokenizer loaded successfully.")
        return self.pipeline

    def summarize(
        self,
        text: str,
        max_length: int = None,
        min_length: int = None,
        do_sample: bool = False
    ) -> str:
        """
        Generate a concise summary of the input text.

        Args:
            text (str): Input text (transcript) to summarize
            max_length (int): Maximum token length for the summary
            min_length (int): Minimum token length for the summary
            do_sample (bool): Whether to use sampling (True = more creative)

        Returns:
            str: Summarized text
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for summarization.")
            return ""

        max_len = max_length or SUMMARY_MAX_LENGTH
        min_len = min_length or SUMMARY_MIN_LENGTH

        # Chunk long texts (BART max input is ~1024 tokens)
        chunks = self._chunk_text(text, max_chunk_chars=3000)
        logger.info(f"Summarizing {len(chunks)} chunk(s) of text...")

        summaries = []
        pipeline = self.load_pipeline()

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i + 1}/{len(chunks)}...")
            result = pipeline(
                chunk,
                max_length=max_len,
                min_length=min_len,
                do_sample=do_sample
            )
            summaries.append(result[0]["summary_text"])

        # Merge chunk summaries
        if len(summaries) == 1:
            final_summary = summaries[0]
        else:
            # Re-summarize merged summaries if multiple chunks
            merged = " ".join(summaries)
            if len(merged) > 3000:
                final_result = pipeline(
                    merged[:3000],
                    max_length=max_len,
                    min_length=min_len,
                    do_sample=do_sample
                )
                final_summary = final_result[0]["summary_text"]
            else:
                final_summary = merged

        logger.info("Summary generated successfully.")
        return final_summary.strip()

    def get_key_points(self, text: str, num_points: int = 5) -> list:
        """
        Extract key bullet points from the text (simple extractive approach).

        Args:
            text (str): Input text
            num_points (int): Number of key points to extract

        Returns:
            list: List of key point strings
        """
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 30]
        # Score sentences by length (as a simple heuristic)
        scored = sorted(sentences, key=len, reverse=True)
        return scored[:num_points]

    @staticmethod
    def _chunk_text(text: str, max_chunk_chars: int = 3000) -> list:
        """
        Split text into manageable chunks for the model.

        Args:
            text (str): Full input text
            max_chunk_chars (int): Maximum characters per chunk

        Returns:
            list: List of text chunk strings
        """
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0

        for word in words:
            current_len += len(word) + 1
            current_chunk.append(word)
            if current_len >= max_chunk_chars:
                chunks.append(" ".join(current_chunk))
                current_chunk = []
                current_len = 0

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks if chunks else [text]
