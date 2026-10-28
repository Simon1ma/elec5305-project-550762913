# Audio Processing Report 2: Submission Verification

Verified: 29 October 2026. Author: Yixiang Ma. Student ID: 550762913.

## Scope and Outcome

The supplied **ELEC5305 Audio Processing Reports Instructions**, including its final submission checklist, is the controlling specification. The three supplied lab report samples were used as presentation references, not as a requirement to repeat every sample experiment.

No blocking omission was found in the checked Report 2 package. This is a technical and submission-format audit, not a prediction of the marker's grade or a check of additional Canvas-only requirements. It does not complete the separate Final Project.

## Requirement Checks

| Requirement | Evidence | Outcome |
| --- | --- | --- |
| Required numbered structure | All sections 2.1 through 2.8 are present. | Pass |
| Title and author information | Topic, full name, SID, and submission date are included; no emblem or abstract. | Pass |
| Focused objective and course relevance | Temporal modulation filtering, STFT reconstruction, and CWT analysis of recorded speech. | Pass |
| Method and important parameters | Dataset, resampling, Hann window, hop, log floor, reflected padding, masks, evaluation interval, and wavelet settings are documented. | Pass |
| Mathematical presentation | Seven native Live Editor equations render in the exported PDF. | Pass |
| Processing block diagram | Figure 1 precedes the detailed analysis code. | Pass |
| Annotated, modular MATLAB implementation | Short executable report blocks call the included `r2_*.m` helpers. | Pass |
| Meaningful results | Calibration, three mask settings, reconstructed spectra, numerical fidelity, envelope comparison, and CWT inspection. | Pass |
| Figure presentation | Seven figures inspected in the final PDF; English labels, units, captions, and comparison scales. | Pass |
| Discussion and conclusion | Parameter effects, original-phase limitations, boundary effects, and single-utterance scope are interpreted. | Pass |
| References and source acknowledgement | Eight numbered references, dataset attribution, source hash, and input licence. | Pass |
| Live Script and corresponding PDF | Saved executed `.mlx` plus native MATLAB PDF export, with code visible. | Pass |
| Required inputs and helpers | The ZIP contains 15 files, including the input recording and all custom helper functions. | Pass |
| Exact submission naming | `Report2 YixiangMa/`, `Report2 YixiangMa.mlx`, `Report2 YixiangMa.pdf`, and `Report2 YixiangMa.zip`. | Pass |
| Independent reproducibility | Final ZIP extracted to a new folder and run in a new MATLAB process with the default MATLAB path restored. | Pass |
| Language | Report prose, source comments, and labels are English; no CJK text found in the PDF or submitted text sources. | Pass |

## Executed Verification

- Tested environment: MATLAB R2026a Update 5, Signal Processing Toolbox, and Wavelet Toolbox.
- The fresh extracted folder did not contain `generated/` before execution. All seven figures and the numerical results were regenerated using only the submitted inputs and toolbox functions.
- The executed Live Script finished with ready status and no stored error output.
- Six report-level numerical assertions passed, including near-exact reconstruction, transform round trip, constant preservation, known 4/16 Hz calibration, and inverse-transform reality.
- `check_report2()` additionally passed three non-frame-aligned signal lengths, odd/even modulation grids, finite-output checks, and mask bounds.
- Reproduced non-baseline metrics agreed with the original values exactly. Bypass SNR remained above 280 dB; small floating-point variations there are not physical enhancement gains.
- The final 11-page PDF was rendered and inspected; no clipping or overlapping plot labels was observed.
- A prose-only revision shortened the report's text from 1,778 to 1,626 words across 18 paragraphs. Structure, executable blocks, input audio, helpers, all seven equations, citations, references, and saved numerical outputs were checked against commit `038c1d4` and retained. The revised ZIP was tested again independently.

## Comparison with the Samples

The report follows the examples' useful pattern of context, method, executable code, figures, interpretation, conclusion, and references. It uses the explicit 2.1-2.8 numbering in the current instructions even where the samples use unnumbered headings. It does not carry over sample placeholders, unrelated demonstrations, or unprovided helper dependencies.

The experiment is deliberately narrower than the broad samples: it tests one recorded utterance across three temporal modulation settings with controlled transform checks. No instruction requires reproducing every resampling, modulation, feature-extraction, or synthesis example appearing in the samples.

## Remaining Limitations and Optional Polish

- The Methodology prose is approximately 359 words, including equation explanations and the diagram caption, reduced from 448 words. This is still above the indicative 150-300 range. The instructions explicitly state there is no strict overall word limit; retaining parameter and symbol definitions avoids making the shorter text ambiguous.
- Native Live Editor pagination splits some captions/text and leaves the last two references on page 11. The figures and formulas are intact; an exact sample page count is not specified.
- Results concern one public development utterance and offline processing. They do not establish generalisation, denoising improvement, real-time operation, or human intelligibility.
- The student should review and understand the submitted method and conclusions. Optional listening was not used as experimental evidence.

## Submitted Package

[Download the ZIP](<../submissions/Report2 YixiangMa.zip>) | [View the PDF](<../Report2 YixiangMa/Report2 YixiangMa.pdf>) | [Live Script and sources](<../Report2 YixiangMa/>)

- Size: 4,124,185 bytes.
- SHA256: `a48fdcf6a08d6d0efe1630ece103561c43ceee046607c29b2dbbc12a1b48ca09`.
- Regenerable MAT files, listening outputs, temporary logs, and unrelated Report 1/Final Project changes are not part of this submission package.
