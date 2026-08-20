# 第一阶段：原视频动态母版取证

只在有可读取参考视频时执行。本阶段的目的不是生成故事板，而是建立可追溯的“原视频动态母版”：以整秒画格连续表达原片的光影、构图、动作、运镜、转场、声音与销售节奏。

## 固定执行顺序

1. 运行 `scripts/probe_video.py`，写入 `evidence/video_probe.json`。
2. 有音轨时运行 `scripts/transcribe_audio.py`，保留 WAV 与带时间戳转写；再运行 `scripts/align_transcript.py` 对齐镜头。
3. 运行 `scripts/extract_frames.py <video> --out evidence/raw-second-frames --interval 1.0`。帧名必须可解析其原片时间；此目录不是 `MF` 输入，禁止据此创建接触表、镜头表或 Batch。
4. **立即从原始帧目录的最后一帧开始连续向前检查。**仅当它们同时满足“位于视频终端”“纯黑/近黑、平台下载尾卡或只含平台水印/账号 UI/搜索框”“无商品、主体动作、有效画面、需保留文字或声音”时，才停止扫描。将扫描到的完整连续无效尾段一次性移入 `evidence/excluded-tail-frames/`，建立 `evidence/tail-trim.json`，再将其余有效帧移入 `evidence/master-frames/`。不得先生成含尾卡的接触表、`MF` 映射、镜头表或 Batch，再回头补裁尾。主体画面仍存在时的角落水印不能裁尾，只能在后续局部移除。
5. 在每个硬切、匹配切、遮挡切、推拉、甩镜、快速手部接触或其他无法由整秒格确认的动态边界附近补抽取证帧，存入 `evidence/transition-evidence/`。补帧只解释动态，不增加最终母版格。
6. 运行 `scripts/make_contact_sheet.py`，仅为已经裁尾完成的 `evidence/master-frames/` 生成逐秒接触表。
7. 以画面、动作、商品状态、口播、屏幕文字、镜头运动和销售任务的实际变化划分连续 `S` 镜头，写入 `evidence/source_shots.json`。
8. 写入 `evidence/reference_style_profile.json` 和 `dynamic-master-breakdown-report.md`；报告同时记载原始时长、有效时长以及（适用时）裁尾依据。

## 每秒母版格

为有效参考范围内的每个 `MF01...MF_last` 记录：原片时间窗口、代表帧时间、文件路径、所属 `S` 镜头、构图、景别、主体距离、场景、可见商品/主体状态、完整动作相位、光线与阴影、镜头运动、进入下一格的转场、口播/OCR/声音证据和置信度。有效内容最后不足 1 秒的尾段仍建立一个尾格，并精确记录其较短的时间窗口；已确认裁掉的平台黑屏/尾卡不建格。

`evidence/tail-trim.json` 仅在裁尾时创建，至少包含：`status: "trimmed"`、`original_duration`、`effective_source_start`、`effective_source_end`、`trimmed_source_start`、`trimmed_source_end`、`reason`、`evidence_frame_paths`。裁剪范围必须是原片的连续末尾，且 `effective_source_end == trimmed_source_start`。

相邻格之间必须描述“运动如何连续”，不能仅写静态画面：例如手从哪里进入、接触点如何保持、镜头向何方向移动、光线如何延续、硬切的下一落点是什么。镜头边界由内容变化决定，绝不由 1 秒间隔决定。

## 原片风格与动态特征

`reference_style_profile.json` 必须包含原生 `source_resolution`、`source_aspect_ratio`、`capture_style`、`platform_aesthetic`、`subject_camera_distance`、`composition_discipline`、`lighting`、`white_balance`、`exposure`、`contrast`、`sharpness`、`motion_blur`、`camera_stability`、`depth_of_field`、`image_degradation`、`style_fingerprint` 与 `anti_style_constraints`。

其中 `style_fingerprint` 是一段可直接下传的完整正向指令，具体锁定原片的画幅取景、平台质感、机位、镜头运动、压缩、模糊、曝光、构图、主体距离和真实光影；`anti_style_constraints` 只写原片证据明确排除的视觉方向。二者不能用“高级”“电影感”“UGC”等泛化词替代，且必须在后续 storyboard-image prompts 中逐字保留。

## 原视频动态母版拆解报告

报告必须依时间顺序写出：技术元数据、原语言转写、自然英文翻译、OCR/屏幕文字、音乐/环境声/音效、钩子拆解、销售逻辑、镜头表、风格指纹、每秒格的动态描述、转场链，以及“可原样保留 / 必须替换 / 因商品事实不兼容而调整”的清单。事实、推断和低置信度内容分别标记。

无参考视频时不创建任何原片证据或伪造字段；改写 `plan/creative-brief.md`，并为原创的每秒格提供相同字段结构。
