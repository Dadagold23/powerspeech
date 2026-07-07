"""
Performance Evaluation Module (evaluator.py)

Evaluates the quality of:
- Transcription: Word Error Rate (WER), Character Error Rate (CER)
- Summarization: ROUGE-1, ROUGE-2, ROUGE-L scores

Objective 5: Evaluate the performance of the system using sample audio inputs.

Author: [Your Name]
Date: 2026
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class EvaluationModule:
    """
    Computes quantitative evaluation metrics for transcription and
    summarization quality.

    Metrics:
    - WER  (Word Error Rate)       - jiwer
    - CER  (Character Error Rate)  - jiwer
    - ROUGE-1, ROUGE-2, ROUGE-L    - rouge-score
    """

    def __init__(self):
        self._load_libs()
        logger.info("EvaluationModule initialized.")

    def _load_libs(self):
        """Lazy import evaluation libraries."""
        try:
            import jiwer
            from rouge_score import rouge_scorer
            self.jiwer = jiwer
            self.rouge_scorer = rouge_scorer
            self._libs_ready = True
        except ImportError as e:
            logger.error(f"Missing evaluation library: {e}. Run: pip install jiwer rouge-score")
            self._libs_ready = False

    def evaluate_transcription(
        self,
        reference: str,
        hypothesis: str
    ) -> dict:
        """
        Evaluate transcription quality using WER and CER.

        Args:
            reference (str): Ground truth transcription
            hypothesis (str): System-generated transcription

        Returns:
            dict: {
                'WER': float,   # Word Error Rate (0.0 = perfect)
                'CER': float,   # Character Error Rate
                'WER_pct': str, # WER as percentage string
                'CER_pct': str
            }
        """
        if not self._libs_ready:
            return {"error": "jiwer not installed"}

        # Normalize text
        transform = self.jiwer.Compose([
            self.jiwer.ToLowerCase(),
            self.jiwer.RemovePunctuation(),
            self.jiwer.Strip(),
            self.jiwer.ReduceToListOfListOfWords()
        ])

        wer = self.jiwer.wer(reference, hypothesis)
        cer = self.jiwer.cer(reference, hypothesis)

        results = {
            "WER": round(wer, 4),
            "CER": round(cer, 4),
            "WER_pct": f"{wer * 100:.2f}%",
            "CER_pct": f"{cer * 100:.2f}%"
        }

        logger.info(f"Transcription Evaluation: WER={results['WER_pct']}, CER={results['CER_pct']}")
        return results

    def evaluate_summarization(
        self,
        reference_summary: str,
        generated_summary: str
    ) -> dict:
        """
        Evaluate summarization quality using ROUGE metrics.

        Args:
            reference_summary (str): Human-written reference summary
            generated_summary (str): AI-generated summary

        Returns:
            dict: {
                'ROUGE-1': {'precision', 'recall', 'fmeasure'},
                'ROUGE-2': {'precision', 'recall', 'fmeasure'},
                'ROUGE-L': {'precision', 'recall', 'fmeasure'}
            }
        """
        if not self._libs_ready:
            return {"error": "rouge-score not installed"}

        scorer = self.rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"],
            use_stemmer=True
        )
        scores = scorer.score(reference_summary, generated_summary)

        results = {
            "ROUGE-1": {
                "precision": round(scores["rouge1"].precision, 4),
                "recall":    round(scores["rouge1"].recall, 4),
                "fmeasure":  round(scores["rouge1"].fmeasure, 4)
            },
            "ROUGE-2": {
                "precision": round(scores["rouge2"].precision, 4),
                "recall":    round(scores["rouge2"].recall, 4),
                "fmeasure":  round(scores["rouge2"].fmeasure, 4)
            },
            "ROUGE-L": {
                "precision": round(scores["rougeL"].precision, 4),
                "recall":    round(scores["rougeL"].recall, 4),
                "fmeasure":  round(scores["rougeL"].fmeasure, 4)
            }
        }

        logger.info(
            f"Summarization Evaluation: "
            f"ROUGE-1={results['ROUGE-1']['fmeasure']}, "
            f"ROUGE-2={results['ROUGE-2']['fmeasure']}, "
            f"ROUGE-L={results['ROUGE-L']['fmeasure']}"
        )
        return results

    def run_batch_evaluation(
        self,
        test_cases: list,
        report_path: str = None
    ) -> dict:
        """
        Run evaluation across multiple test cases and generate a report.

        Args:
            test_cases (list): List of dicts:
                [
                    {
                        'audio_file': str,
                        'reference_transcript': str,
                        'hypothesis_transcript': str,
                        'reference_summary': str,
                        'generated_summary': str
                    },
                    ...
                ]
            report_path (str): Optional path to save JSON report

        Returns:
            dict: Aggregated evaluation results
        """
        all_wer = []
        all_cer = []
        all_r1 = []
        all_r2 = []
        all_rl = []
        detailed = []

        for case in test_cases:
            audio = case.get("audio_file", "unknown")
            trans_result = self.evaluate_transcription(
                case["reference_transcript"],
                case["hypothesis_transcript"]
            )
            summ_result = self.evaluate_summarization(
                case["reference_summary"],
                case["generated_summary"]
            )

            all_wer.append(trans_result.get("WER", 0))
            all_cer.append(trans_result.get("CER", 0))
            all_r1.append(summ_result.get("ROUGE-1", {}).get("fmeasure", 0))
            all_r2.append(summ_result.get("ROUGE-2", {}).get("fmeasure", 0))
            all_rl.append(summ_result.get("ROUGE-L", {}).get("fmeasure", 0))

            detailed.append({
                "audio_file": audio,
                "transcription": trans_result,
                "summarization": summ_result
            })

        def avg(lst):
            return round(sum(lst) / len(lst), 4) if lst else 0

        aggregate = {
            "total_cases": len(test_cases),
            "avg_WER": avg(all_wer),
            "avg_CER": avg(all_cer),
            "avg_ROUGE1_F": avg(all_r1),
            "avg_ROUGE2_F": avg(all_r2),
            "avg_ROUGEL_F": avg(all_rl),
            "evaluated_at": datetime.now().isoformat(),
            "detailed": detailed
        }

        if report_path:
            Path(report_path).parent.mkdir(parents=True, exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(aggregate, f, indent=4)
            logger.info(f"Evaluation report saved: {report_path}")

        return aggregate

    def format_report(self, results: dict) -> str:
        """
        Format evaluation results as a human-readable string.

        Args:
            results (dict): Output from run_batch_evaluation()

        Returns:
            str: Formatted report
        """
        lines = [
            "=" * 50,
            "  SYSTEM PERFORMANCE EVALUATION REPORT",
            "=" * 50,
            f"  Total Test Cases : {results.get('total_cases', 'N/A')}",
            f"  Evaluated At     : {results.get('evaluated_at', 'N/A')}",
            "",
            "  --- TRANSCRIPTION METRICS ---",
            f"  Average WER      : {results.get('avg_WER', 'N/A')} ({results.get('avg_WER', 0)*100:.2f}%)",
            f"  Average CER      : {results.get('avg_CER', 'N/A')} ({results.get('avg_CER', 0)*100:.2f}%)",
            "",
            "  --- SUMMARIZATION METRICS (F-Measure) ---",
            f"  Avg ROUGE-1      : {results.get('avg_ROUGE1_F', 'N/A')}",
            f"  Avg ROUGE-2      : {results.get('avg_ROUGE2_F', 'N/A')}",
            f"  Avg ROUGE-L      : {results.get('avg_ROUGEL_F', 'N/A')}",
            "=" * 50
        ]
        return "\n".join(lines)
