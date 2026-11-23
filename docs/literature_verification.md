# MEMCOLLAPSE: Literature Verification Report

Verification date: 2026-11-23. Every item below was checked against a primary page (official conference site, ACL Anthology, arXiv abstract page, ICML/ICLR virtual site, or publisher). Nothing was accepted from memory alone. Status legend:

- **VERIFIED**: exists, and the claimed title/venue/content match the primary source.
- **PARTIALLY MATCHES**: exists, but at least one claimed detail (venue, framing, scope) is wrong or misleading.
- **NOT FOUND**: no primary source located.

---

## A. ACL 2027 Call for Papers

| Claim | Status | Evidence |
|---|---|---|
| Special theme "Homogenization and Knowledge Collapse in LLMs" | **VERIFIED** | CFP lists the theme "Homogenization and knowledge collapse in LLMs". It invites work on low-diversity outputs and "generative monoculture" ("LLMs tend to collapse diversity in their outputs"). Long or short papers; empirical, theoretical, survey and position papers are all accepted. |
| ARR submission deadline 4 January 2027 | **VERIFIED** | 4 Jan 2027, 11:59pm UTC-12 (AoE). Commitment, notification and camera-ready dates were still TBA when checked. |
| Kyoto, 17–22 Aug 2027 | **VERIFIED** | Kyoto, Japan. Tutorials on 17 Aug, workshops on 18–19 Aug, main conference on 20–22 Aug 2027. |
| Page limit 8 pages (long) | **VERIFIED** | Long papers have 8 pages and short papers 4. Camera-ready versions get one extra page (9 and 5). A Limitations section is required, as in ARR. |

URLs: https://2027.aclweb.org/ (home page: location and dates) and https://2027.aclweb.org/calls/main/ (first call for main conference papers, posted 29 Sep 2026).

**Fit with MEMCOLLAPSE:** the project fits the theme directly. It studies homogenization inside an agent's own memory over time, which is a within-system form of knowledge collapse.

---

## B. Claimed papers

### B1. "What and Whose Knowledge?" (claimed EMNLP 2026, epistemic diversity across 27 LLMs). Status: **VERIFIED**
- **Exact title:** *What and Whose Knowledge? Measuring Epistemic Diversity in Large Language Models*
- **Authors:** Dustin Wright, Sarah Masud, Jared Moore, Srishti Yadav, Maria Antoniak, Peter Ebert Christensen, Chan Young Park, Isabelle Augenstein
- **Venue:** EMNLP 2026 (main), pp. 35186–35203. Anthology: https://aclanthology.org/2026.emnlp-main.1542/
- **arXiv:** 2510.04226. Later arXiv versions use the title *Epistemic Diversity and Knowledge Collapse in Large Language Models*. Cite the Anthology title.
- **Summary:** The authors measure epistemic diversity, meaning variation in real-world claims, across 27 LLMs, 155 topics and 12 countries (1.7M responses, about 70M claims). Diversity has risen over time but every model stays below a web-search baseline. Larger models are less diverse, RAG helps, and country-specific knowledge skews toward English sources.
- **Relation:** This paper measures diversity across models in single-shot answers. MEMCOLLAPSE measures how claims are lost inside one agent's memory over successive update rounds. The claim-level measurement method can be reused.

### B2. "Beyond Epistemic Collapse" (claimed EMNLP 2026, EVIRAG). Status: **VERIFIED**
- **Exact title:** *Beyond Epistemic Collapse: Disagreement-Aware Scientific Retrieval-Augmented Generation*
- **Authors:** Animesh Mishra, Krishang Sharma, Sonia Khetarpaul
- **Venue:** EMNLP 2026 (main), pp. 54964–54985. https://aclanthology.org/2026.emnlp-main.2421/ . Code: https://github.com/amethystani/evirag-bench
- **Summary:** EVIRAG combines adversarial retrieval, claim-level disagreement graphs and multi-view synthesis so that scientific RAG keeps conflicting findings apart instead of collapsing them into one answer. It ships with EVIRAG-BENCH (1,250 queries, 5 domains) and metrics including ContradictionRecall, ViewpointCoverage and a Consensus Collapse Score.
- **Relation:** This is single-step RAG synthesis, not iterative memory. Its Consensus Collapse Score and ViewpointCoverage metrics are useful related work and could serve as baselines.

### B3. "All Languages Matter" (claimed ACL 2026, language bias in multilingual RAG, reranking). Status: **VERIFIED**
- **Exact title:** *All Languages Matter: Understanding and Mitigating Language Bias in Multilingual RAG*
- **Authors:** Dan Wang, Guozhao Mo, Yafei Shi, Cheng Zhang, Bo Zheng, Boxi Cao, Xuanang Chen, Yaojie Lu, Hongyu Lin, Ben He, Xianpei Han, Le Sun
- **Venue:** ACL 2026 (long), pp. 7441–7455. https://aclanthology.org/2026.acl-long.338/ ; arXiv 2604.20199
- **Summary:** Rerankers in multilingual RAG favor English and the query language and filter out useful documents in other languages. The paper proposes LAURA, which aligns rerankers using downstream generation utility as the training signal.
- **Relation:** Only tangential. It concerns language bias in reranking, not memory or compression. Cite it only as an analogy for systematic filtering of non-dominant content, or drop it.

### B4. "Don't Scroll Back" (claimed Findings EMNLP 2026, streaming dialogue summarization, selective memory). Status: **VERIFIED**
- **Exact title:** *Don't Scroll Back: Missing-Evidence Memory for Streaming Dialogue Summarization*
- **Authors:** Hyangsuk Min, Hwanjun Song
- **Venue:** Findings of EMNLP 2026, pp. 22728–22760. https://aclanthology.org/2026.findings-emnlp.1075/ ; arXiv 2608.09043
- **Summary:** The paper defines streaming dialogue summarization: summarize the current window using memory retrieved selectively from a long history under a fixed budget. Its method, ReMEMBER, finds unresolved dependencies in the current window, retrieves the history chunks that resolve them, and condenses them. Histories reach 160K tokens.
- **Relation:** This is budgeted, retrieval-based memory for summarization. It does not study claim loss across repeated rewrites of a memory state. It is a possible strong baseline.

### B5. "Context-Driven Incremental Compression" / C-DIC (claimed ICML 2026). Status: **VERIFIED**
- **Exact title:** *Context-Driven Incremental Compression for Multi-Turn Dialogue Generation*
- **Authors:** Yeongseo Jung, Jaehyeok Kim, Eunseo Jung, Jiachuan Wang, Yongqi Zhang, Ka Chun Cheung, Simon See, Lei Chen
- **Venue:** ICML 2026 poster. https://icml.cc/virtual/2026/poster/63188 ; arXiv 2606.12411
- **Summary:** The method models a dialogue as interleaved topic threads. Each thread keeps a revisable compressed (latent) memory that is updated through a retrieve, revise and write-back loop. Latency and perplexity reportedly stay stable over hundreds of turns, up to 428, with a 7B backbone.
- **Relation:** This is iterative, revisable memory compression, the same kind of mechanism MEMCOLLAPSE stress-tests. The paper evaluates efficiency and perplexity, not which claims survive.

### B6. "Another Turn, Better Output?" (claimed EMNLP 2026, degradation over iterative refinement). Status: **VERIFIED**
- **Exact title:** *Another Turn, Better Output? A Turn-Wise Analysis of Iterative LLM Prompting*
- **Authors:** Shashidhar Reddy Javaji, Bhavul Gauri, Zining Zhu
- **Venue:** EMNLP 2026 (main), pp. 53085–53110. https://aclanthology.org/2026.emnlp-main.2337/ ; arXiv 2509.06770. An earlier version appeared at the NeurIPS 2025 Workshop on Multi-Turn Interactions in LLMs.
- **Summary:** The study runs 12-turn "improve it" loops with 7 models on 450 tasks across ideation, code and math. It finds a "discovery–retention gap": models produce good intermediate outputs and then overwrite them. Code accuracy falls from 40.7% at turn 1 to 2.5% at turn 12.
- **Relation:** This is turn-wise degradation under iterative self-revision. It supports the general claim that repeated rewriting loses information, but it does not track memory, claim frequency or which claims are lost.

### B7. "ReMEMBER" memory architecture. Status: **PARTIALLY MATCHES**
- ReMEMBER exists only as the method inside B4 (*Don't Scroll Back*, Min and Song, Findings EMNLP 2026). No standalone paper or general agent memory architecture with this name was found. It is a gap-conditioned evidence-retrieval and condensation framework for streaming dialogue summarization.
- **Action:** cite it as "ReMEMBER (Min and Song, 2026)" pointing to B4, and do not describe it as a general long-horizon agent memory architecture.

**Bottom line for B:** none of the 7 items is fabricated. Six are fully verified and one (ReMEMBER) is mis-framed. Watch two details: B1 has two titles (use the Anthology one), and B3 is weakly relevant.

---

## C. Closest real prior work (all verified)

### C1. Most threatening to novelty: repeated compaction erases specific content
| # | Reference | Overlap / difference with MEMCOLLAPSE |
|---|---|---|
| 1 | Zerhoudi, Mitrovic, Granitzer. **The Compaction Cliff in Long-Running AI Agent Memory.** CIKM 2026. arXiv 2608.22752. https://arxiv.org/abs/2608.22752 | **Closest overlap.** It measures retention across compaction rounds: Claude Code /compact keeps 53% of safety rules after 1 round and 10% after 5. It proposes a type-aware retention method (Knowledge Triage: TypeCompact, TypeDecompose, TypeRetrieve). Difference: it covers rule types (safety rules versus logs), not claim frequency with content held fixed, and it has no hazard modeling and no minority-view or caveat focus. Its type-aware compaction overlaps the planned importance-constrained method. |
| 2 | Zahn, Chana. **Facts as First Class Objects: Knowledge Objects for Persistent LLM Memory.** arXiv 2603.17781 (2026). https://arxiv.org/abs/2603.17781 | Finds that summarization destroys 60% of facts, that cascading compaction erodes 54% of project constraints while the model stays confident ("goal drift"), and that the pattern holds across 4 frontier models. Difference: it does not manipulate frequency or attribute loss to claim type. Its fix is a structured external store, not constrained compression. Preprint. |
| 3 | Zhu, Lin, Wang, Liu, Li, Chen. **Will My Assistant Remember My Allergy? What Personal LLM Assistants Forget When Conversation Memory Is Compressed.** ACM HumanSys 2026. arXiv 2609.05767 | A safety-critical fact mentioned once (an allergy) survives KV-cache compression only 0–1% of the time when the question is hidden, against 97% with full memory. This directly shows that low-frequency, decision-critical facts are lost. Difference: it studies KV-cache eviction, not text-level rolling summaries, and uses a single compression step rather than rounds. |
| 4 | Zhang et al. **Agentic Context Engineering (ACE): Evolving Contexts for Self-Improving Language Models.** ICLR 2026. arXiv 2510.04618 | Names "context collapse" (iterative rewriting erodes details over time) and "brevity bias". It fixes them with incremental delta updates. Difference: it reports the phenomenon anecdotally as motivation (AppWorld case) and does not measure which claims die or why. |
| 5 | Lee et al. **When Summaries Distort Decisions: Information Fidelity in LLM-Compressed Financial Analysis.** EMNLP 2026 Industry. arXiv 2606.29251 | Compression changes the decision a document supports while staying fluent and plausible. It names "decontextualization", where evidence survives but its caveats are dropped, which is close to MEMCOLLAPSE's caveat-loss hypothesis. Difference: single-pass, finance-only, and no frequency manipulation. |
| 6 | Tamme, Hantel, Khosrawi-Rad. **Whose Voice Survives the Summary? A Voice-Retention Audit of LLM Employee Listening.** HICSS 2027. arXiv 2609.38818 | Field evidence that retention depends on frequency: a concern mentioned once is dropped 86% of the time, and sentiment has no effect once frequency is controlled. This is the same independent variable as MEMCOLLAPSE. Difference: single-pass summarization of real data with no control over content, and no iteration. |
| 7 | Tian et al. **RGMem: Renormalization Group-inspired Memory Evolution for Language Agents.** ICML 2026. arXiv 2510.16392 | Argues that LLM memory summarizers act like a "majority vote" that smooths away recent or minority signals, and separates dominant history from corrections. Difference: the claim motivates a method. Survival is not measured in a controlled way. |
| 8 | Lam et al. **Governing Evolving Memory in LLM Agents (SSGM framework).** arXiv 2603.11768 (2026) | A conceptual taxonomy that names semantic drift from iterative summarization as a memory-governance risk. No controlled measurement. Preprint. |

### C2. Long-term memory systems and benchmarks (the targets and testbeds)
| # | Reference | Overlap / difference |
|---|---|---|
| 9 | Wang et al. **Recursively Summarizing Enables Long-Term Dialogue Memory in LLMs.** Neurocomputing (accepted). arXiv 2308.15022 | The standard rolling-summary memory and a natural system to test. It reports gains in consistency, not what is lost. |
| 10 | Packer et al. **MemGPT: Towards LLMs as Operating Systems.** arXiv 2310.08560 (2023) | Hierarchical memory with recursive summary eviction. A system under test. |
| 11 | Zhong et al. **MemoryBank: Enhancing LLMs with Long-Term Memory.** arXiv 2305.10250; AAAI 2024 | Ebbinghaus-style forgetting, where forgetting is designed in. A contrast case: intended forgetting versus unintended erasure. |
| 12 | Xu et al. **A-MEM: Agentic Memory for LLM Agents.** NeurIPS 2025. arXiv 2502.12110 | Self-organizing memory notes that evolve over time. A system under test. |
| 13 | Chhikara et al. **Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory.** arXiv 2504.19413 (2025) | Extract, update and consolidate memory, including UPDATE/DELETE operations that can overwrite minority claims. A system under test. |
| 14 | Maharana et al. **Evaluating Very Long-Term Conversational Memory of LLM Agents (LoCoMo).** ACL 2024. https://aclanthology.org/2024.acl-long.747 | Benchmark of question answering over long dialogues. It does not vary claim frequency and has no per-round survival analysis. |
| 15 | Wu et al. **LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory.** ICLR 2025. arXiv 2410.10813 | Five memory abilities, including knowledge updates. It measures end-task QA accuracy, not erosion over rounds. |
| 16 | Hu, Wang, McAuley. **Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions (MemoryAgentBench).** ICLR 2026. arXiv 2507.05257 | Feeds data incrementally and tests four competencies, including selective forgetting and conflict resolution (FactConsolidation). It is the closest benchmark design but does not hold content fixed while varying frequency. |
| 17 | Min, Song. **Don't Scroll Back** (B4) and Jung et al. **C-DIC** (B5) | Budgeted and iterative memory methods. Possible baselines. |

### C3. Minority-view and perspective erasure in summarization (single-pass)
| # | Reference | Overlap / difference |
|---|---|---|
| 18 | Zhang et al. **Fair Abstractive Summarization of Diverse Perspectives.** NAACL 2024. https://aclanthology.org/2024.naacl-long.187 | PerspectiveSumm, plus fairness metrics for how well summaries represent groups. Single-pass. Its metrics can be reused for minority-claim coverage. |
| 19 | Huang, Fayek, Zhang. **Bias in Opinion Summarisation from Pre-training to Adaptation: A Case Study in Political Bias.** EACL 2024. https://aclanthology.org/2024.eacl-long.63 | Measures stance bias in abstractive opinion summarizers. Single-pass. |
| 20 | Dash, Shandilya, et al. **Summarizing User-generated Textual Content: Motivation and Methods for Fairness in Algorithmic Summaries.** CSCW 2019. arXiv 1810.09147 (building on Shandilya, Ghosh, Ghosh, "Fairness of Extractive Text Summarization", WWW 2018 Companion, doi 10.1145/3184558.3186947) | The origin of fairness work in summarization. Extractive and single-pass. |
| 21 | Zhu, Yang, Bakker, Pentland, Pei. **Can AI Truly Represent Your Voice in Deliberations? (DeliberationBank).** arXiv 2510.05154 | Across 18 LLMs, finds persistent under-representation of minority positions and order effects in summaries of deliberations. Single-pass. |
| 22 | Aghaebe, Apekey, Williams, Moosavi. **Faithful Summarisation under Disagreement via Belief-Level Aggregation.** arXiv 2601.04889 (2026) | Documents majority bias and proposes belief merging before generation. Relevant to the method design, since structured intermediate representations help. Preprint. |
| 23 | Peters, Chin-Yee. **Generalization bias in large language model summarization of scientific research.** Royal Society Open Science 12(4):241776, 2025. arXiv 2504.00025 | LLM summaries overgeneralize, dropping hedges and scope conditions in 26–73% of cases, and are about 5 times more likely than humans to do so. Strong single-pass evidence for caveat loss. |

### C4. Collapse, homogenization and transmission chains (theory and analogues)
| # | Reference | Overlap / difference |
|---|---|---|
| 24 | Shumailov et al. **AI models collapse when trained on recursively generated data.** Nature 631:755–759, 2024. doi 10.1038/s41586-024-07566-y | The tails of a distribution disappear first under recursion. This is the conceptual parent of MEMCOLLAPSE, but it concerns training rather than inference-time memory. |
| 25 | Peterson. **AI and the Problem of Knowledge Collapse.** AI & Society (2025). arXiv 2404.03502 | A societal-level model of tail loss through cheap AI access. Theoretical, with no memory mechanism. |
| 26 | Wu, Black, Chandrasekaran. **Generative Monoculture in Large Language Models.** ICLR 2025. arXiv 2407.02209 | Output distributions narrow relative to training data (for example, uniformly positive reviews of books with mixed reception). Single-shot. |
| 27 | Perez et al. **When LLMs Play the Telephone Game: Cultural Attractors as Conceptual Tools to Evaluate LLMs in Multi-turn Settings.** ICLR 2025. arXiv 2407.04503 | Iterated LLM transmission chains converge on attractors in toxicity, positivity, difficulty and length. It measures text-level properties, not the survival of individual claims. |
| 28 | Acerbi, Stubbersfield. **Large language models show human-like content biases in transmission chain experiments.** PNAS 120(44):e2313790120, 2023 | In serial reproduction, LLMs preferentially keep negative, social, threat-related and stereotype-consistent content. This is the closest existing content-level survival analysis in chains, but it is story retelling, not memory with decision-critical claims. |
| 29 | Liu et al. **Lost in the Middle: How Language Models Use Long Contexts.** TACL 2024. arXiv 2307.03172 | Positional bias is a confound. MEMCOLLAPSE must control claim position so that frequency effects are not position effects. |
| 30 | Javaji, Gauri, Zhu. **Another Turn, Better Output?** (B6) | Degradation over iterative self-revision, framed as a discovery–retention gap. |

Not adopted (could not be characterized from primary pages): arXiv 2609.35302, *Narrowing the Horizon: Quantifying Topic Saliency Shifts in Generative Monoculture*. Its abstract could not be retrieved, so check it before citing.

---

## D. Novelty assessment (honest)

**Already done (do not claim as novel):**
1. *"Iterative summarization or compaction loses information."* This is established and named: "context collapse" (ACE, ICLR 2026), the "Compaction Cliff" (CIKM 2026: 53% then 10% of safety rules after 1 and 5 rounds), and goal drift under cascading compaction (Zahn and Chana 2026). Round-by-round retention curves already exist.
2. *"Rare or once-mentioned critical facts are lost under compression."* Shown for KV-cache compression (allergy facts, HumanSys 2026) and for single-pass summarization (concerns mentioned once are dropped 86% of the time, HICSS 2027).
3. *"Summaries under-represent minority views and drop hedges or caveats."* Well documented for single-pass summarization (Zhang et al. NAACL 2024; DeliberationBank; Peters and Chin-Yee 2025; "decontextualization" in Lee et al. EMNLP 2026 Industry).
4. *"Type- or importance-aware compaction mitigates loss."* Knowledge Triage (Compaction Cliff) already reports 96% retention of safety rules over 5 rounds with type-specific retention. ACE delta updates and structured Knowledge Objects are also direct competitors. A generic "importance-constrained compressor" alone will look incremental.
5. Transmission-chain content biases in LLMs (Acerbi and Stubbersfield 2023; Perez et al. ICLR 2025).

**What remains open (the defensible narrow angle):**
- **A causal frequency manipulation in iterative text memory, with content held fixed.** No paper found varies a claim's mention frequency (1, 2, 4, ... occurrences) while keeping its content, position and wording constant, then tracks its survival round by round in a rolling text memory. Existing evidence is either observational (HICSS), single-step (HumanSys) or varies claim type rather than frequency (Compaction Cliff).
- **Survival and hazard modeling at the claim level.** No found work fits survival models (Kaplan–Meier curves, Cox or discrete-time hazards) with covariates such as frequency, claim role (minority view, condition or caveat, rare warning, majority claim), position, recency and compressor model. This yields interpretable effect sizes such as "a caveat has an X-fold hazard relative to its main claim", which retention percentages cannot give.
- **Separating fluency and factuality from coverage.** The core paradox is that memory stays fluent and has no hallucinations while its epistemic coverage collapses. Showing this requires measuring the two jointly, with FActScore-style precision alongside claim recall weighted toward minority and caveat claims. Prior compaction work reports recall alone.
- **Decision-critical downstream harm.** Tie claim death to decision flips, where an agent acts differently once a caveat or warning is gone. Lee et al. do this for single-pass finance only.
- **Scope distinct from the Compaction Cliff:** the Compaction Cliff covers rules in agent configuration files. MEMCOLLAPSE would cover epistemic content (minority views, conditions, warnings) inside conversational or episodic memory, and minority views are not rules a type classifier can tag.
- **Method framing that is more defensible:** a provenance-anchored compressor in which each memory claim keeps pointers to its sources and its count of supporting versus dissenting mentions, plus a survival constraint (for example, caveat claims are never merged without their parent). Compare it head-to-head against Knowledge Triage-style typing, ACE delta updates, and belief-level aggregation (Aghaebe et al.). Without those baselines, reviewers will say the method is already done.

**Recommended positioning sentence:** "Prior work shows that agent memory compaction loses rules and facts over rounds, and that single-pass summaries under-represent minority and hedged content. We give the first controlled, causal account of *which* claims die in iterative LLM memory and *how fast*. We manipulate claim frequency with content held fixed and model claim-level hazards across update rounds. We show that memory can stay fluent and factually precise while it systematically loses minority, conditional and warning claims."

**Risks:** (i) The Compaction Cliff (CIKM 2026) is the reviewer's first counterexample, so cite it prominently and set MEMCOLLAPSE apart from it. (ii) The ACL 2027 theme will draw many diversity and collapse papers, so the memory-dynamics and hazard-model angle is what makes the paper distinct. (iii) Several close items (2603.17781, 2603.11768, 2601.04889, 2510.05154) are unrefereed preprints, so label them as preprints.

---

## References (BibTeX, verified items only)

```bibtex
@inproceedings{wright-etal-2026-whose,
  title     = {What and Whose Knowledge? Measuring Epistemic Diversity in Large Language Models},
  author    = {Wright, Dustin and Masud, Sarah and Moore, Jared and Yadav, Srishti and Antoniak, Maria and Christensen, Peter Ebert and Park, Chan Young and Augenstein, Isabelle},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026},
  pages     = {35186--35203},
  address   = {Budapest, Hungary},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2026.emnlp-main.1542/}
}

@inproceedings{mishra-etal-2026-beyond,
  title     = {Beyond Epistemic Collapse: Disagreement-Aware Scientific Retrieval-Augmented Generation},
  author    = {Mishra, Animesh and Sharma, Krishang and Khetarpaul, Sonia},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026},
  pages     = {54964--54985},
  address   = {Budapest, Hungary},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2026.emnlp-main.2421/}
}

@inproceedings{wang-etal-2026-all,
  title     = {All Languages Matter: Understanding and Mitigating Language Bias in Multilingual {RAG}},
  author    = {Wang, Dan and Mo, Guozhao and Shi, Yafei and Zhang, Cheng and Zheng, Bo and Cao, Boxi and Chen, Xuanang and Lu, Yaojie and Lin, Hongyu and He, Ben and Han, Xianpei and Sun, Le},
  booktitle = {Proceedings of the 64th Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2026},
  pages     = {7441--7455},
  address   = {San Diego, California},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2026.acl-long.338/}
}

@inproceedings{min-song-2026-dont,
  title     = {Don't Scroll Back: Missing-Evidence Memory for Streaming Dialogue Summarization},
  author    = {Min, Hyangsuk and Song, Hwanjun},
  booktitle = {Findings of the Association for Computational Linguistics: EMNLP 2026},
  year      = {2026},
  pages     = {22728--22760},
  address   = {Budapest, Hungary},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2026.findings-emnlp.1075/}
}

@inproceedings{jung2026cdic,
  title     = {Context-Driven Incremental Compression for Multi-Turn Dialogue Generation},
  author    = {Jung, Yeongseo and Kim, Jaehyeok and Jung, Eunseo and Wang, Jiachuan and Zhang, Yongqi and Cheung, Ka Chun and See, Simon and Chen, Lei},
  booktitle = {Proceedings of the 43rd International Conference on Machine Learning (ICML)},
  year      = {2026},
  note      = {arXiv:2606.12411},
  url       = {https://arxiv.org/abs/2606.12411}
}

@inproceedings{javaji-etal-2026-another,
  title     = {Another Turn, Better Output? A Turn-Wise Analysis of Iterative {LLM} Prompting},
  author    = {Javaji, Shashidhar Reddy and Gauri, Bhavul and Zhu, Zining},
  booktitle = {Proceedings of the 2026 Conference on Empirical Methods in Natural Language Processing},
  year      = {2026},
  pages     = {53085--53110},
  address   = {Budapest, Hungary},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2026.emnlp-main.2337/}
}

@inproceedings{zerhoudi2026compaction,
  title     = {The Compaction Cliff in Long-Running {AI} Agent Memory},
  author    = {Zerhoudi, Saber and Mitrovic, Jelena and Granitzer, Michael},
  booktitle = {Proceedings of the 35th ACM International Conference on Information and Knowledge Management (CIKM)},
  year      = {2026},
  doi       = {10.1145/3799682.3840567},
  note      = {arXiv:2608.22752}
}

@article{zahn2026facts,
  title   = {Facts as First Class Objects: Knowledge Objects for Persistent {LLM} Memory},
  author  = {Zahn, Oliver and Chana, Simran},
  journal = {arXiv preprint arXiv:2603.17781},
  year    = {2026}
}

@inproceedings{zhu2026allergy,
  title     = {Will My Assistant Remember My Allergy? What Personal {LLM} Assistants Forget When Conversation Memory Is Compressed},
  author    = {Zhu, Lichen and Lin, Yueqian and Wang, Yiheng and Liu, Yudong and Li, Hai Helen and Chen, Yiran},
  booktitle = {Proceedings of ACM HumanSys 2026},
  year      = {2026},
  doi       = {10.1145/3842436.3843817},
  note      = {arXiv:2609.05767}
}

@inproceedings{zhang2026ace,
  title     = {Agentic Context Engineering: Evolving Contexts for Self-Improving Language Models},
  author    = {Zhang, Qizheng and Hu, Changran and Upasani, Shubhangi and Ma, Boyuan and Hong, Fenglu and Kamanuru, Vamsidhar and Rainton, Jay and Wu, Chen and Ji, Mengmeng and Li, Hanchen and Thakker, Urmish and Zou, James and Olukotun, Kunle},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2026},
  note      = {arXiv:2510.04618}
}

@inproceedings{lee2026summaries,
  title     = {When Summaries Distort Decisions: Information Fidelity in {LLM}-Compressed Financial Analysis},
  author    = {Lee, Hoyoung and Park, Suhwan and Lee, Seunghan and Seo, Jun and Lee, Jaehoon and Yoo, Sungdong and Kim, Minjae and Na, CheolWon and Wang, Zhangyang and Golkhou, Zach and Kim, Minkyu and Sabanis, Sotirios and Lopez-Lira, Alejandro and Mehta, Dhagash and Lee, Soonyoung and Choi, Chanyeol and Ahn, Wonbin and Lee, Yongjae},
  booktitle = {Proceedings of EMNLP 2026: Industry Track},
  year      = {2026},
  note      = {arXiv:2606.29251}
}

@inproceedings{tamme2027voice,
  title     = {Whose Voice Survives the Summary? A Voice-Retention Audit of {LLM} Employee Listening},
  author    = {Tamme, Thilo and Hantel, Anton and Khosrawi-Rad, Bijan},
  booktitle = {Proceedings of the 60th Hawaii International Conference on System Sciences (HICSS)},
  year      = {2027},
  note      = {arXiv:2609.38818}
}

@inproceedings{tian2026rgmem,
  title     = {{RGMem}: Renormalization Group-inspired Memory Evolution for Language Agents},
  author    = {Tian, Ao and Lu, Yunfeng and Fan, Xinxin and Wang, Changhao and Zhou, Lanzhi and Zhang, Yeyao and Liu, Yanfang},
  booktitle = {Proceedings of the 43rd International Conference on Machine Learning (ICML)},
  year      = {2026},
  note      = {arXiv:2510.16392}
}

@article{lam2026ssgm,
  title   = {Governing Evolving Memory in {LLM} Agents: Risks, Mechanisms, and the Stability and Safety Governed Memory ({SSGM}) Framework},
  author  = {Lam, Chingkwun and Li, Jiaxin and Zhang, Lingfei and Zhao, Kuo},
  journal = {arXiv preprint arXiv:2603.11768},
  year    = {2026}
}

@article{wang2023recursively,
  title   = {Recursively Summarizing Enables Long-Term Dialogue Memory in Large Language Models},
  author  = {Wang, Qingyue and Fu, Yanhe and Cao, Yanan and Wang, Shuai and Tian, Zhiliang and Ding, Liang},
  journal = {Neurocomputing},
  year    = {2025},
  note    = {arXiv:2308.15022}
}

@article{packer2023memgpt,
  title   = {{MemGPT}: Towards {LLMs} as Operating Systems},
  author  = {Packer, Charles and Wooders, Sarah and Lin, Kevin and Fang, Vivian and Patil, Shishir G. and Stoica, Ion and Gonzalez, Joseph E.},
  journal = {arXiv preprint arXiv:2310.08560},
  year    = {2023}
}

@inproceedings{zhong2024memorybank,
  title     = {{MemoryBank}: Enhancing Large Language Models with Long-Term Memory},
  author    = {Zhong, Wanjun and Guo, Lianghong and Gao, Qiqi and Ye, He and Wang, Yanlin},
  booktitle = {Proceedings of the AAAI Conference on Artificial Intelligence},
  year      = {2024},
  note      = {arXiv:2305.10250}
}

@inproceedings{xu2025amem,
  title     = {{A-MEM}: Agentic Memory for {LLM} Agents},
  author    = {Xu, Wujiang and Liang, Zujie and Mei, Kai and Gao, Hang and Tan, Juntao and Zhang, Yongfeng},
  booktitle = {Advances in Neural Information Processing Systems (NeurIPS)},
  year      = {2025},
  note      = {arXiv:2502.12110}
}

@article{chhikara2025mem0,
  title   = {{Mem0}: Building Production-Ready {AI} Agents with Scalable Long-Term Memory},
  author  = {Chhikara, Prateek and Khant, Dev and Aryan, Saket and Singh, Taranjeet and Yadav, Deshraj},
  journal = {arXiv preprint arXiv:2504.19413},
  year    = {2025}
}

@inproceedings{maharana-etal-2024-evaluating,
  title     = {Evaluating Very Long-Term Conversational Memory of {LLM} Agents},
  author    = {Maharana, Adyasha and Lee, Dong-Ho and Tulyakov, Sergey and Bansal, Mohit and Barbieri, Francesco and Fang, Yuwei},
  booktitle = {Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2024},
  pages     = {13851--13870},
  address   = {Bangkok, Thailand},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2024.acl-long.747}
}

@inproceedings{wu2025longmemeval,
  title     = {{LongMemEval}: Benchmarking Chat Assistants on Long-Term Interactive Memory},
  author    = {Wu, Di and Wang, Hongwei and Yu, Wenhao and Zhang, Yuwei and Chang, Kai-Wei and Yu, Dong},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2410.10813}
}

@inproceedings{hu2026memoryagentbench,
  title     = {Evaluating Memory in {LLM} Agents via Incremental Multi-Turn Interactions},
  author    = {Hu, Yuanzhe and Wang, Yu and McAuley, Julian},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2026},
  note      = {arXiv:2507.05257}
}

@inproceedings{zhang-etal-2024-fair,
  title     = {Fair Abstractive Summarization of Diverse Perspectives},
  author    = {Zhang, Yusen and Zhang, Nan and Liu, Yixin and others and Zhang, Rui},
  booktitle = {Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2024},
  pages     = {3404--3426},
  address   = {Mexico City, Mexico},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2024.naacl-long.187}
}

@inproceedings{huang-etal-2024-bias,
  title     = {Bias in Opinion Summarisation from Pre-training to Adaptation: A Case Study in Political Bias},
  author    = {Huang, Nannan and Fayek, Haytham and Zhang, Xiuzhen},
  booktitle = {Proceedings of the 18th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)},
  year      = {2024},
  pages     = {1041--1055},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2024.eacl-long.63}
}

@inproceedings{shandilya2018fairness,
  title     = {Fairness of Extractive Text Summarization},
  author    = {Shandilya, Anurag and Ghosh, Kripabandhu and Ghosh, Saptarshi},
  booktitle = {Companion Proceedings of The Web Conference 2018},
  year      = {2018},
  pages     = {97--98},
  doi       = {10.1145/3184558.3186947}
}

@article{zhu2025deliberation,
  title   = {Can {AI} Truly Represent Your Voice in Deliberations? A Comprehensive Study of Large-Scale Opinion Aggregation with {LLMs}},
  author  = {Zhu, Shenzhe and Yang, Shu and Bakker, Michiel A. and Pentland, Alex and Pei, Jiaxin},
  journal = {arXiv preprint arXiv:2510.05154},
  year    = {2025}
}

@article{aghaebe2026belief,
  title   = {Faithful Summarisation under Disagreement via Belief-Level Aggregation},
  author  = {Aghaebe, Favour Yahdii and Apekey, Tanefa and Williams, Elizabeth and Moosavi, Nafise Sadat},
  journal = {arXiv preprint arXiv:2601.04889},
  year    = {2026}
}

@article{peters2025generalization,
  title   = {Generalization bias in large language model summarization of scientific research},
  author  = {Peters, Uwe and Chin-Yee, Benjamin},
  journal = {Royal Society Open Science},
  volume  = {12},
  number  = {4},
  pages   = {241776},
  year    = {2025},
  doi     = {10.1098/rsos.241776}
}

@article{shumailov2024collapse,
  title   = {{AI} models collapse when trained on recursively generated data},
  author  = {Shumailov, Ilia and Shumaylov, Zakhar and Zhao, Yiren and Papernot, Nicolas and Anderson, Ross and Gal, Yarin},
  journal = {Nature},
  volume  = {631},
  pages   = {755--759},
  year    = {2024},
  doi     = {10.1038/s41586-024-07566-y}
}

@article{peterson2025knowledge,
  title   = {{AI} and the Problem of Knowledge Collapse},
  author  = {Peterson, Andrew J.},
  journal = {AI \& Society},
  year    = {2025},
  note    = {arXiv:2404.03502}
}

@inproceedings{wu2025monoculture,
  title     = {Generative Monoculture in Large Language Models},
  author    = {Wu, Fan and Black, Emily and Chandrasekaran, Varun},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2407.02209}
}

@inproceedings{perez2025telephone,
  title     = {When {LLMs} Play the Telephone Game: Cultural Attractors as Conceptual Tools to Evaluate {LLMs} in Multi-turn Settings},
  author    = {Perez, J{\'e}r{\'e}my and others},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2025},
  note      = {arXiv:2407.04503}
}

@article{acerbi2023transmission,
  title   = {Large language models show human-like content biases in transmission chain experiments},
  author  = {Acerbi, Alberto and Stubbersfield, Joseph M.},
  journal = {Proceedings of the National Academy of Sciences},
  volume  = {120},
  number  = {44},
  pages   = {e2313790120},
  year    = {2023}
}

@article{liu2024lost,
  title   = {Lost in the Middle: How Language Models Use Long Contexts},
  author  = {Liu, Nelson F. and Lin, Kevin and Hewitt, John and Paranjape, Ashwin and Bevilacqua, Michele and Petroni, Fabio and Liang, Percy},
  journal = {Transactions of the Association for Computational Linguistics},
  volume  = {12},
  pages   = {157--173},
  year    = {2024}
}
```

Notes on BibTeX: entries that use `others` (Zhang et al. 2024 and Perez et al. 2025) should be filled with the full author lists from the Anthology or arXiv `.bib` export before submission. Shumailov et al.'s co-author list, the TACL volume and pages for Liu et al., and the AAAI venue for MemoryBank are standard records but were not re-fetched field by field. Check them against the publisher's BibTeX export.
