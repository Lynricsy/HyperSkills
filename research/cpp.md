# cpp 调研记录

> 正式正文与4份参考已完成，评测唯一入口为 [`skills/cpp/evals/`](../skills/cpp/evals/)。下文保留Phase A/B当时记录；用户继续建设后的最新结论见文末，内容交付不等于已证明增益。

## 调研日期与检索途径

- 调研/复核日期：2026-09-12。
- GitHub 已登录 API；code search `filename:SKILL.md "cpp"`，再查仓库递归树、原始 contents（base64解码）和仓库 metadata。所有候选原文都实读，不以搜索摘要打分。
- 补查 github/awesome-copilot、Jeffallan/claude-skills、affaan-m/everything-claude-code 与 isocpp/CppCoreGuidelines。镜像用于发现来源，最终回到原仓。
- GitHub 仓库字段来自 `gh api repos/<owner>/<repo>`；目录/文件固定在本次树 HEAD。首次 cppcheatsheet 请求 TCP timeout，合理重试成功；未匿名回退，未遇认证失败或限流。
- 非 GitHub 官方资料直接读 clang.llvm.org、cmake.org、eel.is 标准工作草案；CMake 的 PUBLIC/PRIVATE 又经 Context7 `/kitware/cmake` 交叉。
- 新鲜度只按仓库 pushed_at 评分，不把仓库活跃虚称为每个 skill 文件最近修改。

## 立项裁决

**通过通常门槛，不援引官方厂商特例。** 15个真实候选（13个 SKILL.md、2个 Copilot instructions），来自11个仓库；其中第1/3/15项分别来自三个独立、六个月内活跃、≥8分的上游，贡献分别是构造失败/RAII、异步所有权、并发测试与诊断。仅窄选这些能力，不合入百科正文、项目风格或基础语法。

GitHub官方身份不等于C++维护方。Core Guidelines是权威专家校验来源而不是技能仓库，且许可证限制公开再分发，不能用它套用官方特例。两个ECC镜像不计为独立证据。INCLUDE表示通过数值线，不意味着全部文本可以合入；正确性0、过期、越界和许可仍有否决权。

## 候选表

评分：权威0–3 / 新鲜0–3 / 具体0–3 / 正确0–3 / 许可0–2；≥8 INCLUDE，5–7 MAYBE，≤4 REJECT。正确性仅代表下面列出的三项抽查，不是全部代码已验证。许可分是仓库声明强度，不是派生来源权利保证。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | crazyguitar/cppcheatsheet `skills/cpp/SKILL.md` | [原文](https://github.com/crazyguitar/cppcheatsheet/blob/a33b7e756f6c2811e80ae73165bd2a053289bac3/skills/cpp/SKILL.md) | 285 | 2026-09-02T05:42:02Z | MIT | C/C++全集路由；仅RAII失败路径有用 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE（窄选） | 不合入百科、CUDA或WebFetch流程；只选RAII异常边界 |
| 2 | crazyguitar/cppcheatsheet `skills/readable-cpp/SKILL.md` | [原文](https://github.com/crazyguitar/cppcheatsheet/blob/a33b7e756f6c2811e80ae73165bd2a053289bac3/skills/readable-cpp/SKILL.md) | 285 | 2026-09-02T05:42:02Z | MIT | C/C++/Rust/CUDA可读性 | 1 | 3 | 1 | 1 | 2 | 8 | INCLUDE（不选） | 机械两层缩进/三参数规则；noexcept一概化需修正 |
| 3 | margelo/react-native-skills `skills/cpp/SKILL.md` | [原文](https://github.com/margelo/react-native-skills/blob/1e9e17be6f41c838db472d6a4b943fc26355a3be/skills/cpp/SKILL.md) | 167 | 2026-08-21T15:00:55Z | NONE | 通用所有权、异步与Nitro | 2 | 3 | 3 | 3 | 0 | 11 | INCLUDE（窄选） | 原生集成团队；剥离Nitro和mutex最后手段的绝对化 |
| 4 | davidYichengWei/agentic-engineering-framework `skills/std-cpp/SKILL.md` | [原文](https://github.com/davidYichengWei/agentic-engineering-framework/blob/1f7ac0fb9aa61791c7c22f1a1d1719f70347b4e4/skills/std-cpp/SKILL.md) | 158 | 2026-03-25T05:13:37Z | MIT | Google风格C++17 | 1 | 1 | 1 | 3 | 2 | 8 | INCLUDE（不选） | 仅项目风格，禁止C++2a不是生态事实；不用于核心合成 |
| 5 | Jeffallan/claude-skills `skills/cpp-pro/SKILL.md` | [原文](https://github.com/Jeffallan/claude-skills/blob/882ef55e377dbf9a4dbe496bb41ac6ccd0e555cf/skills/cpp-pro/SKILL.md) | 11427 | 2026-08-07T20:19:18Z | MIT | 现代C++/并发/构建 | 1 | 2 | 3 | 0 | 2 | 8 | REJECT | 无安全回收的lock-free pop；可复制coroutine owner双destroy |
| 6 | github/awesome-copilot `instructions/cmake-vcpkg.instructions.md` | [原文](https://github.com/github/awesome-copilot/blob/7568a482ce2df38f8965ab5336a3220db796a4ba/instructions/cmake-vcpkg.instructions.md) | 38915 | 2026-09-11T20:50:01Z | MIT | CMake/vcpkg项目指令 | 3 | 3 | 1 | 3 | 2 | 12 | INCLUDE（reference） | 非C++维护方官方；manifest/绝对路径是项目条件，内容太短 |
| 7 | github/awesome-copilot `instructions/cpp-language-service-tools.instructions.md` | [原文](https://github.com/github/awesome-copilot/blob/7568a482ce2df38f8965ab5336a3220db796a4ba/instructions/cpp-language-service-tools.instructions.md) | 38915 | 2026-09-11T20:50:01Z | MIT | Copilot工具操作 | 3 | 3 | 1 | 1 | 2 | 10 | REJECT（范围） | 绑定GetSymbol*工具；把空结果当已找到symbol无从保证 |
| 8 | testdino-hq/google-styleguides-skills `cpp/SKILL.md` | [原文](https://github.com/testdino-hq/google-styleguides-skills/blob/8674a2a2186a02f86852e061f6166a500ae30f7c/cpp/SKILL.md) | 10 | 2026-02-25T10:55:24Z | MIT | Google样式转载 | 1 | 0 | 1 | 1 | 2 | 5 | REJECT（过期） | 2026-02-25已超6月；非Google官方，const不等于线程安全 |
| 9 | ericrisco/rsc-harness `skills/cpp/SKILL.md` | [原文](https://github.com/ericrisco/rsc-harness/blob/322b95f96b64c98d3ab5f1c610ff61e85e57f4cb/skills/cpp/SKILL.md) | 82 | 2026-09-10T16:07:34Z | MIT | C++20/23、UB、CMake | 1 | 3 | 3 | 0 | 2 | 9 | REJECT | 所有moved-from读都算UB、sanitizer证明无UB两处错误 |
| 10 | zhuangwenhui/CodingSkills `cpp-code-format/SKILL.md` | [原文](https://github.com/zhuangwenhui/CodingSkills/blob/40f58763d53e7314c9fd76ba3ff76ae7bc1bbf04/cpp-code-format/SKILL.md) | 82 | 2026-06-14T15:20:19Z | MIT | ShapeReconstruction局部风格 | 1 | 2 | 3 | 3 | 2 | 11 | INCLUDE（reference） | 边界与版本矩阵明确；不可带入用户未选的项目格式 |
| 11 | zig-whatwg/crane `skills/cpp/SKILL.md` | [原文](https://github.com/zig-whatwg/crane/blob/292958cc18a01df2bd4cbf8bb9166b59b763851a/skills/cpp/SKILL.md) | 11 | 2026-01-22T22:30:31Z | MIT | V8/Zig FFI | 1 | 0 | 2 | 1 | 2 | 6 | REJECT（过期） | 无frontmatter，V8内部指针转换假设不适用通用C++ |
| 12 | JantonioFC/skillsbank `.kiro/skills/cpp-coding-standards/SKILL.md` | [原文](https://github.com/JantonioFC/skillsbank/blob/512bb7e8cc67c53699d7697edf4376d0f4d64007/.kiro/skills/cpp-coding-standards/SKILL.md) | 6 | 2026-08-04T04:06:46Z | MIT | Core Guidelines镜像 | 1 | 2 | 2 | 1 | 2 | 8 | INCLUDE（reference） | 与ECC重复；底层Core许可未被MIT覆盖，不重复计入立项 |
| 13 | JantonioFC/skillsbank `.kiro/skills/cpp-testing/SKILL.md` | [原文](https://github.com/JantonioFC/skillsbank/blob/512bb7e8cc67c53699d7697edf4376d0f4d64007/.kiro/skills/cpp-testing/SKILL.md) | 6 | 2026-08-04T04:06:46Z | MIT | C++测试镜像 | 1 | 2 | 2 | 1 | 2 | 8 | INCLUDE（reference） | ECC镜像不重复合入；sanitizer选项可同时开启ASan/TSan |
| 14 | affaan-m/everything-claude-code `skills/cpp-coding-standards/SKILL.md` | [原文](https://github.com/affaan-m/everything-claude-code/blob/c4904e3f6381df934fc00bffb0afa7a1f8dae0e3/skills/cpp-coding-standards/SKILL.md) | 256612 | 2026-09-12T03:45:33Z | MIT | Core Guidelines编码规则 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE（reference） | 直接派生权威指南，许可保守隔离；Buffer默认move遗留size不变量 |
| 15 | affaan-m/everything-claude-code `skills/cpp-testing/SKILL.md` | [原文](https://github.com/affaan-m/everything-claude-code/blob/c4904e3f6381df934fc00bffb0afa7a1f8dae0e3/skills/cpp-testing/SKILL.md) | 256612 | 2026-09-12T03:45:33Z | MIT | CMake/CTest/并发测试 | 1 | 3 | 3 | 1 | 2 | 10 | INCLUDE（窄选） | 复用确定性/诊断清单语义；拒绝ASan+TSan兼容性遗漏 |

## 深度审查

对排名靠前的7项（#1、#3、#6、#7、#9、#10、#15）通读正文并浏览适用引用；另外为发现严重错误深读#5的并发/内存/协程引用。

1. **cppcheatsheet/cpp**：两字段frontmatter有效，但description把C、C++、CUDA、Shell、Rust、面试全混在一起，必须缩窄。实读 `references/guidelines.md`、浏览完整主题路由 `references/structure.md`；继续打开RAII页面的构造失败/异常保证章节。通用“先WebFetch网站”绑定agent且不证明正确性，删除。只保留尚待基线验证的构造失败、成员清理与借用边界主题，其他百科全部不选。
2. **Margelo cpp**：短正文、无本技能references；树确认不存在LICENSE，按NONE。原生集成团队的异步所有权比通用清单具体：禁止用sleep补竞态、回调调用时锁的重入风险、线程归属，值得窄选。Nitro Promise、HybridObject、JS线程全部转给react-native；`mutex last resort`是架构偏好，不泛化为C++安全规则。
3. **GitHub cmake-vcpkg instruction**：只有description/applyTo，不能直接安装为跨agent skill。无references。manifest mode是原项目事实，绝对OpenCV路径也是局部建议；只用于发现构建配置边界，不作为核心正文来源。
4. **GitHub CppTools instruction**：通读，工具列表/调用工作流/错误恢复高度绑定Copilot；无references。主张IntelliSense能查“ALL”但它只能看活动配置，空结果也不能推出symbol已找到。整个能力属于工具接入，不纳入通用cpp。
5. **rsc-harness cpp**：正文加3个一层引用，结构清楚，但frontmatter tags/recommends/origin非标准，跨skill路径与02-DOCS写入有宿主副作用。实读UB、move、CMake引用相关部分：把合法moved-from观察判错、把sanitizer阴性说成证明、vector noexcept规则省略不可复制类型分支。正确性0直接拒绝；不因覆盖面好而带病重写。
6. **CodingSkills cpp-code-format**：通读正文，浏览22562字符研究引用（版本条件、来源优先级、格式与冲突表）。明确只对ShapeReconstruction生效、与DeformSim的C++17边界是优点；Google/Intel/LLVM风格不能当全生态不变量。无宿主工具绑定，但工作区名字是硬绑定。本主题只reference其边界意识，禁止导入其100列/项目命名。
7. **ECC cpp-testing**：正文通读、树确认无技能内references。origin已放metadata，基本可移植。大部分基础TDD/mock样板没有信息增益；只选条件同步、目标级诊断、CTest实际发现的验证语义。ASan/TSan布尔选项可同时开，没有互斥，需要裁决；Catch2“header-only”不能推广到v3。无需复制例子或强制GoogleTest。

**附加深读**：Jeffallan `references/concurrency.md` 的pop在并发线程可能持有old_head时delete，注释只提ABA不足以修复reclamation；`modern-cpp.md` Generator拥有handle却可复制，两个析构会destroy同一协程；`memory-performance.md` PoolAllocator示例只接受n=1却用于vector，不能作为通用vector allocator。正文看似成熟，引用恰恰更危险，直接拒绝。

## 正确性抽查（每候选三项）

抽查依据编号：D1=[栈展开/构造失败](https://eel.is/c++draft/except.ctor)，D2=[string_view布局/失效](https://eel.is/c++draft/string.view.template)，D3=[vector失效与异常保证](https://eel.is/c++draft/vector.modifiers)，D4=[数据竞争与同步](https://eel.is/c++draft/intro.races)，D5=[moved-from](https://eel.is/c++draft/lib.types.movedfrom)，D6=[UBSan范围](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)，D7=[TSan限制](https://clang.llvm.org/docs/ThreadSanitizer.html)，D8=[CMake使用需求](https://cmake.org/cmake/help/latest/command/target_compile_definitions.html)，D9=[CMake标准元特性](https://cmake.org/cmake/help/latest/manual/cmake-compile-features.7.html)，D10=[GoogleTest发现](https://cmake.org/cmake/help/latest/module/GoogleTest.html)，D11=[join/detach](https://eel.is/c++draft/thread.thread.member)。专家旁证为Core Guidelines R.1、CP.22、CP.42，API读取其原文而不复制。

| 候选 | 样本1 | 样本2 | 样本3 | 正确分 |
|---|---|---|---|---|
| #1 | 普通非委托构造失败只析构已完成成员，D1，对 | RAII已构造成员异常清理，D1，对 | view不拥有底层，D2，对 | 3 |
| #2 | RAII资源，D1，对 | 小值/借用不等于拥有，D2，对 | 所有move直接noexcept，D3的可抛move分支反例，错 | 1 |
| #3 | 明确跨异步生命周期，D2/D11，对 | sleep不能产生所需同步，D4，对 | 未知callback持锁重入风险，CP.22，对 | 3 |
| #4 | self-contained头文件作为项目约定可行，D9，对 | C++17作为项目最低模式可行，D9，对 | 按值throw/引用catch可行，D1，对；“Google现行标准”不采信 | 3 |
| #5 | RAII wrapper禁copy，对D1 | 并发pop立即delete存在生命周期冲突，D4，错 | owning Generator隐式copy双destroy，D1生命周期所有权，错 | 0 |
| #6 | presets管理cache是局部配置建议非语言限制，可接受 | 关注CMake policies，D9，对 | 跨编译器须分工具能力，D9，对；manifest/OpenCV不作为通用事实 | 3 |
| #7 | 活动预处理配置会影响分析，D8/D9，对 | 保留准确文件行号，对 | 空结果必然表示symbol存在，无依据且可能配置不含定义，错 | 1 |
| #8 | smart pointer表达所有权，D1，对 | string/auto例子可行，D2，对 | const宣称线程安全忽略其他别名/可变状态，D4，错 | 1 |
| #9 | TSan数据竞争用途，D7，对 | 所有moved-from读取都错误，D5，错 | ASan/UBSan证明覆盖路径无UB，D6/D7，错 | 0 |
| #10 | C++20项目模式与C++17共享代码分开，D9，对 | 需求只应要求最低模式，D9，对 | 项目API不得擅改为新标准，D9，对；未复核其全部MSVC市场/版本数字，不采入 | 3 |
| #11 | RAII禁copy示例，对D1 | view借用，D2，对 | opaque V8 pointer重新解释为Local包装对象无有效类型/生命周期证明，错；未验证V8 API不合入 | 1 |
| #12/#14 | RAII资源，D1，对 | 条件变量谓词CP.42，对 | Buffer默认move留下size但清空unique_ptr，复制moved-from实例会从空指针copy非零size，错 | 1 |
| #13/#15 | gtest_discover_tests运行可执行文件而非只扫描源码，D10，对 | TSan是race检测D7，对 | 独立ASan/TSan选项无互斥可产生不支持组合，D7及工具要求，错 | 1 |

这些是源码/文档审查，不是编译执行结论；按本批合同没有运行任何候选代码。

## 冲突与裁决

| 冲突点 | 上游主张 | 裁决 | 依据 |
|---|---|---|---|
| sanitizer阴性 | rsc称prove no UB | 阴性只说明本次插桩/输入未报告；区分未覆盖检查、未插桩依赖与逻辑错误 | D6/D7 |
| 已移动对象 | rsc只许析构/赋值 | 按类型契约和操作前置条件判断，不把empty()/size()等无前置条件观察判成UB | D5 |
| vector move noexcept | 多份要求一律noexcept | 按真实是否抛出声明；不可复制元素的可抛move与异常保证单列，不能为性能撒谎 | D3 |
| 所有权 vs borrowed value | 把按值传递笼统等同安全 | string_view/span值仍是借用；异步必须证明owner和失效点，snapshot要求不同于保活 | D2/D3/D11 |
| mutex最后手段 | Margelo偏向owner thread | 先遵从现有并发模型；普通共享状态默认可用mutex，不强迫executor重构 | D4、CP.22 |
| 原子就正确 | 泛化sanitizer验证 | atomic消除数据竞争不保证跨atomic协议顺序；release/acquire必须读取同一次发布 | D4 |
| target宏影响ABI | 泛化PRIVATE偏好 | public header受影响宏是usage requirement，producer和consumer都需要则PUBLIC；链接成功不是ODR证明 | D8 |
| C++标准支持 | C++23 since GCC11等粗粒度表 | 记录编译器、stdlib、模式与feature-test宏/最小编译探针；cxx_std_23只要求模式不保证每个feature | D9 |
| 官方指南许可 | API NOASSERTION、社区MIT转载 | Core Guidelines仅内部用途许可，Proprietary/reference；直接重述的ECC standards也reference，不以镜像洗许可 | 实读LICENSE全文 |

## 最终合入清单（Phase C候选，非已合入声明）

| id | 上游 | relation计划 | 贡献 |
|---|---|---|---|
| cppcheatsheet | crazyguitar/cppcheatsheet `skills/cpp`、`docs/notes/cpp/cpp_raii.rst` | merged | 只重写构造失败/异常清理主题，不复制百科与代码 |
| margelo-cpp | margelo/react-native-skills `skills/cpp` | merged | 非拥有视图、回调/异步所有权、锁外调用；无许可证按本仓宽松署名政策且不逐字复制 |
| ecc-cpp-testing | affaan-m/everything-claude-code `skills/cpp-testing` | merged | 只重写确定性并发场景和诊断覆盖清单，排除错误选项组合/样板 |
| cpp-core-guidelines | isocpp/CppCoreGuidelines `CppCoreGuidelines.md`、`LICENSE` | reference | 权威规则交叉检查，Proprietary，禁止公开派生文本 |
| cmake-docs | cmake.org文档D8–D10 | reference | usage requirements、标准模式不保证具体feature、测试发现 |
| clang-docs | clang.llvm.org D6/D7 | reference | 检查边界、未插桩代码和数据竞争区别 |
| cpp-draft | eel.is D1–D5/D11 | reference | 标准语义校验；工作草案不能冒充所有C++17新增API都可用 |

三份merged候选的存在只证明调研门通过；Phase C仅保留有实跑缺口支撑的段落。SOURCES.yaml此时不标记任何内容已merged，等基线后由同一owner填写。

### 原文固定提交

- `crazyguitar/cppcheatsheet` `master` @ `a33b7e756f6c2811e80ae73165bd2a053289bac3`
- `margelo/react-native-skills` `main` @ `1e9e17be6f41c838db472d6a4b943fc26355a3be`
- `davidYichengWei/agentic-engineering-framework` `main` @ `1f7ac0fb9aa61791c7c22f1a1d1719f70347b4e4`
- `Jeffallan/claude-skills` `main` @ `882ef55e377dbf9a4dbe496bb41ac6ccd0e555cf`
- `github/awesome-copilot` `main` @ `7568a482ce2df38f8965ab5336a3220db796a4ba`
- `testdino-hq/google-styleguides-skills` `main` @ `8674a2a2186a02f86852e061f6166a500ae30f7c`
- `ericrisco/rsc-harness` `main` @ `322b95f96b64c98d3ab5f1c610ff61e85e57f4cb`
- `zhuangwenhui/CodingSkills` `main` @ `40f58763d53e7314c9fd76ba3ff76ae7bc1bbf04`
- `zig-whatwg/crane` `main` @ `292958cc18a01df2bd4cbf8bb9166b59b763851a`
- `JantonioFC/skillsbank` `main` @ `512bb7e8cc67c53699d7697edf4376d0f4d64007`
- `affaan-m/everything-claude-code` `main` @ `c4904e3f6381df934fc00bffb0afa7a1f8dae0e3`
- `isocpp/CppCoreGuidelines` master @ `33bcd015997f0d8e0fa0202eb66254a16f59ad8f`；API 45313 stars，pushed_at 2026-08-06T15:54:13Z，NOASSERTION→实读LICENSE后Proprietary。不是候选skill，不充数。

## 具体建设范围

面向现有C++17/20/23项目，不擅升标准。优先：owner/borrow图和失效点、普通/委托构造失败差异、move不变量、发布协议与数据竞争分离、ODR/ABI宏与CMake传递闭包、sanitizer选择及阴性边界。编译器/标准库支持逐特性核实，不写“GCC某版本支持所有C++23”。若基线无缺口，不为了覆盖列表补写百科。

明确排除Unreal Gameplay/GAS/复制、嵌入式板级工具链、GPU训练、C语言全集、风格争论、手写通用allocator和lock-free算法教程。通用C++在unreal skill中已排除，无需改动其正文。

## 基线缺口

**首轮基线已实跑，无已证实缺口。** Main运行 `openai/gpt-5.6-sol`、`medium`，worker实读四份result与前三份answer，并核对events中的修复/编译/运行结果及负例官方Unreal文档调用。原有场景保留，新增场景5考查lazy coroutine的closure/frame生命周期与未启动取消，不提前宣布它会失败。

| 场景 | 当前准备状态 | 预期区分度，不是实测失败 |
|---|---|---|
| queued-labels | C++17单文件，事件循环先排队后drain | view值捕获+短字符串容器移动/修改+局部销毁；真正snapshot不能只延长生命周期 |
| packet ABI | CMake3.20/C++17四文件，无下载依赖 | PRIVATE宏跨target静默改变布局，未来consumer靠usage requirement自动获得定义 |
| publication | C++17单文件，两个atomic/两个thread | 全atomic没有data race但协议不足，TSan可沉默；必须建立发布链而非工具崇拜 |
| Unreal near-miss | 无夹具，skills=[] | C++关键词不能盖过RPC/GAS领域边界 |
| deferred-report（5） | C++20单文件已实跑，基线5/5 | lazy coroutine持有frame不等于持有closure；取消前从未resume也须释放所有权 |

夹具现归档于 `research/evals/cpp/files/`，实跑时位于 `skills/cpp/evals/files/`；runner扁平复制后CMake引用本目录的packet文件，文件名无冲突。四个正例总计7个小夹具；没有隐藏外部项目、网络包或答案文件。Main原夹具冒烟：queued-labels触发ASan heap-use-after-free；packet成功构建但运行stack smashing；publication本机输出42（不证明协议）；deferred-report编译成功但运行报告`report expired while queued`并退出1。协程夹具保留完成和取消的所有权检查，先显式检查weak_ptr失效，不依赖UB偶然崩溃；不需要额外库或线程。

## 评测结果

| 场景 | 模型 | 有/无skill | skill_read | 达成行为 | 备注 |
|---|---|---|---|---|---|
| queued-labels（1） | openai/gpt-5.6-sol medium | 无skill | false | 4/4 | 按值拥有string快照；事件证实alpha/beta与sanitizer构建成功 |
| packet（2） | openai/gpt-5.6-sol medium | 无skill | false | 4/4 | PUBLIC producer契约；两侧-D一致；client=16 library=16 |
| publication（3） | openai/gpt-5.6-sol medium | 无skill | false | 5/5 | 无race≠发布正确；release/acquire链与阴性边界完整 |
| Unreal（4） | openai/gpt-5.6-sol medium | 无skill | false | 2/2 | events显示查询官方Epic RPC/复制/GAS文档，无cpp读取 |
| deferred-report（5） | openai/gpt-5.6-sol medium | 无skill | false | 5/5 | 按值参数进入协程帧；完成和未resume取消均释放；C++20 ASan/UBSan实跑通过 |

逐条评分证据目录：`/tmp/hs-five-20260912/evals/cpp/openai-gpt-5.6-sol-medium/baseline/{1..5}/`。

- **1.1–1.4全达成**：answer.md:5–9识别borrow和销毁；13–21给拥有string并保留defer；25–39给实际sanitizer输出。events的 `call_d1wJf2TYXGnpTKWoqnI0DUNA` 和 `call_5P3JuljJQSELO29DUHGzziEy` 两次工具结果均alpha/beta。它未写“证明所有生命周期安全”，无需强求特定免责声明措辞。
- **2.1–2.4全达成**：answer.md:3–14 PUBLIC与ODR根因；18–25实际编译定义/尺寸；27–29解释链接和sizeof都不足以证明ABI。events `call_0uo4lwDOOrnqhkKoGY6nCf9R` 为verbose构建，`call_6aN9tNDOUoRD0aLxAp2HqsHi` 为client=16 library=16。
- **3.1–3.5全达成**：answer.md:12 relaxed跨对象不足；19–31精确两处修改和同步链；37–41区分ASan/UBSan/TSan边界；45–50只声称实跑普通与ASan+UBSan。events `call_k05MvllK3sPWUoIDes97MmMg` 证实sanitized 42；未运行TSan不是本题失败，它没有谎称运行。无不兼容组合，不为缺少TSan命令强造缺口。
- **4.1–4.2全达成**：result.json skill_read=false；events `call_lZh64UBXukQmk9B4d2Bqf2x9` 解析Unreal文档，后续三个query-docs分别处理RPC、复制条件、GAS；没有泛化为std::atomic/CMake。
- **5.1–5.5全达成**：answer.md:5–24区分closure和frame、按值参数保活及两种释放路径；workspace中的deferred-report.cpp:55–65实际改为独立协程并移动shared_ptr参数，未移除main检查或改为立即执行。events `call_xEbtLcoFDmR9HI2IAEORVCdH` 证实C++20 ASan/UBSan构建运行输出`completion and cancellation release reports`。原始事件的assistant provider/model为openai/gpt-5.6-sol，没有替换评测模型。

结论：首轮15项与追加5项全部达成，当前20/20；不能据此填入任何“模型已经缺失”的规则。新增场景5检验了生产生命周期边界，但仍未形成区分度。当前只完成调研与构建准备，没有有skill组、无增益结论，不进入Phase C或把scope骨架发布为完整skill。下一次重写前须先提供符合真实消费者合同的未达成基线证据；不靠固定措辞或额外工具要求制造失败。

场景5依据：[C++ coroutine definitions](https://eel.is/c++draft/dcl.fct.def.coroutine) 的参数副本初始化早于promise构造、initial_suspend位于函数体之前、destroy释放coroutine state、参数副本在promise之后结束生命周期。工作草案原文已读；使用的协程机制要求C++20。该依据用于设计可判断的场景，不是新正文。

## 备注

- Margelo目录树无LICENSE且API null；不是未经查看就猜MIT。按本仓NONE政策可重写思想，必须在最终SOURCES notes说明不逐字复制。
- Core Guidelines LICENSE明确限定personal/internal business use；不能从其网页复制规则表、例子或通过ECC镜像间接复制。
- 已通过gh递归树定位并固定实读 `docs/notes/cpp/cpp_raii.rst` 的构造失败章节（同a33b7e7提交），与网页核对一致；最终SOURCES应包含该路径，不把移动网页当固定commit内容。
- 官方工作草案章节会前移；前三个正例使用C++17已有语义，新增协程场景要求C++20，后续正文有版本敏感规则须再核实发布标准/工具版本。

## Phase B构建准备交付（历史记录）

当时保留评测与原始故障，临时Scope骨架不计入目录。原5场景与7份夹具现已原样迁入[正式评测目录](../skills/cpp/evals/)，不再维护准备目录副本或骨架恢复命令。用户随后要求正式建设，后续对照按[路线图](../docs/roadmap.md)使用同模型medium与独立输出，保留既有20/20基线事实。

## Phase C 正式建设（2026-09-12）

用户获知上一轮停在Phase B且没有正文后，明确要求“好，正式开始构建skill”。
本轮按该继续建设决定交付完整正文，不再把强基线无缺口作为停笔条件。
上述20/20无skill结果、原始事件路径及历史暂缓裁决完整保留；本节更新的是
建设状态，不把已通过的能力宣称为新增模型收益。有skill组仍待Main统一运行，
当前没有增益结论。

### 实际结构与来源落点

- `skills/cpp/SKILL.md`：framework类别、版本2026.09.12；20条Core rules；
  ownership、concurrency、cross-target build、feature adoption四个具名验证门工作流；
  四个带可观察read-when的一层路由；不扩大到Unreal/GPU/板级或C全集。
- `references/lifetime-and-exceptions.md`：owner/borrow与snapshot区别、vector具体失效、
  普通与委托构造失败、function-try-block、move耦合不变量和真实异常保证。
  重新实读cppcheatsheet的`docs/notes/cpp/cpp_raii.rst`，只重写构造失败主题；
  未采用其vector move必须noexcept的过度断言，也未复制其scope guard代码。
- `references/deferred-work.md`：queue/closure/frame/handle四层生命期、
  owning按值参数先于initial_suspend、取消前从未resume、运行中与外部awaiter撤销、
  完成后frame释放。例子明确为消费项目已有Task的集成片段，不冒充标准task或可独立运行程序。
- `references/concurrency-protocols.md`：状态协议、同一发布的release/acquire链、
  one-shot与可复用消息区别、条件变量谓词、callback重入及shutdown quiescence。
  重新实读Margelo cpp全文，仅重写通用所有权与异步主题；不采Nitro、
  mutex-last-resort或Jeffallan无安全回收的lock-free示例。
- `references/build-and-diagnostics.md`：producer usage requirements、
  PUBLIC/PRIVATE/INTERFACE与static link区别、ABI/ODR及编译器/stdlib/feature probe、
  ASan/UBSan/TSan实测边界和CTest不为空的实际执行。
  重新实读ECC `skills/cpp-testing/SKILL.md`，窄选确定性调度与诊断覆盖思想，
  不复制测试样板、不采ASan+TSan组合，也不采用其Core Guidelines派生standards。
- `SOURCES.yaml`：三个真实merged来源与七个reference记录。三个merged仓库HEAD
  经本次已登录`gh api`重新查询，均与原固定40位提交一致；cppcheatsheet/ECC
  LICENSE全文实读为MIT；Margelo API license仍null，明确NONE、宽松署名重写且无逐字复制。
  Core Guidelines本次只重读LICENSE并核实HEAD，记录路径仅LICENSE，
  Proprietary/reference，不虚称本轮重新读取指南全文，不借MIT镜像洗许可。
- 官方本次实读：工作草案except.ctor、vector.modifiers、lib.types.movedfrom、
  atomics.order、dcl.fct.def.coroutine（含参数副本后半段）；CMake4.1.6
  buildsystem/compile-features相应章节；Clang ASan/UBSan/TSan覆盖和限制章节。
  正文对C++17/20/23标注机制底线，不把草案后续设施泛称C++17可用。

### 交付与未执行项

已恢复`skills/cpp/`正文和四个references；使用目录复制恢复
`research/evals/cpp/`到`skills/cpp/evals/`，没有解析重写原5个定义或7个错误夹具。
原归档路径暂留，由Main独占最终迁移整合。本轮未新增脚本、README或生成NOTICE。
按并行写作合同，未运行格式化、lint、测试、构建、安装、模型评测、全库校验、
check_upstream --pin、提交或推送；示例命令不是本轮实跑证据。
Main后续统一结构检查、实际验证与with-skill评测，不能把本次文档校准写成sanitizer通过。

## Phase D 实际有 skill 审阅（2026-09-12）

本节覆盖原5场、20项 `expected_behavior`，以当前
[`evals.json`](../skills/cpp/evals/evals.json) 原判据逐项评分，不另加关键词、
命令数量或新知识题。正式建设是用户获知强基线后明确要求的交付；
下列结果更新Phase C的“待运行”，不抹去Phase A/B历史裁决。
审阅只读取已有结果、真实工具事件和最终workspace，未重跑模型、编译、测试或安装。

证据路径约定：

- `R/N` = `/tmp/hs-five-build-20260912/evals/cpp/openai-gpt-5.6-sol-medium/skill/N`。
- `W/N` = `/tmp/hs-five-build-20260912/workspaces/cpp-openai-gpt-5.6-sol-medium-skill-N`。
- `A` = 对应 `R/N/answer.md`；`E` = 对应 `R/N/events.jsonl`，数字为物理行号。
  `W` 后文件行号指最终产物，不取同回合中途编辑状态。
- 五份 `result.json` 均记录 `model=openai/gpt-5.6-sol`、
  `thinking=medium`、`baseline=false`；E中assistant的provider/model也均为
  `openai` / `gpt-5.6-sol`。`status=ok`只表示运行结束，不作为评分证明。

### 五场汇总与实际导航

| 场景 | 有skill评分 | 无skill既有评分 | skill_read | 实际读取正文后的references（工具结果行） | 时长 |
|---|---|---|---|---|---|
| 1 queued-labels | 4 pass / 0 partial / 0 fail | 4/4 | true（E28） | lifetime-and-exceptions（E58）、deferred-work（E61） | 148.0s |
| 2 packet ABI | 4 pass / 0 partial / 0 fail | 4/4 | true（E135） | build-and-diagnostics（E168） | 150.0s |
| 3 publication | 5 pass / 0 partial / 0 fail | 5/5 | true（E142） | concurrency-protocols（E180） | 225.8s |
| 4 Unreal near-miss | 2 pass / 0 partial / 0 fail | 2/2 | false | 无cpp正文或reference读取；官方Unreal文档路线 | 272.5s |
| 5 deferred-report | 5 pass / 0 partial / 0 fail | 5/5 | true（E35） | deferred-work（E58） | 143.2s |

四份reference均至少被一个正例实际读到；场景1的双引用分别对应字符失效与
延迟所有权，场景5直接读协程引用。读取是导航诊断，不算行为增益。
负例在cpp可用的with-skill配置下仍为 `skill_read=false`，不是“无技能可读”的
空通过；其E97解析Unreal文档，E153/157/161分别取得RPC、复制条件和GAS资料，
E191还实际读取Epic RPC页面。

### 20项逐项判定

| 条号 | 原预期要点 | 评分 | 决定性证据 |
|---|---|---|---|
| 1.1 | view值捕获仍借用，增长/修改/销毁失效 | pass | A5–10说明地址长度不拥有字符、reserve(1)后重分配、edited破坏快照及局部labels销毁；未把output存活等同labels保活。 |
| 1.2 | callback拥有post时字符快照，仍defer | pass | W/1 `queued-labels.cpp:19–28` 两次初始化捕获实际复制string；25仍修改首标签，10–13仍排队后drain，31–37保留alpha/beta检查；E533实际输出alpha/beta。 |
| 1.3 | 不以reserve/view值捕获/可变容器shared owner代替修复 | pass | A12–22给owning string方案；W/1仍有reserve(1)，修复不依赖容器保活或改变其修改。 |
| 1.4 | C++17输出与ASan诊断，阴性非全性质证明 | pass | A26–39的命令与输出由E527调用/E533结果独立支持：`g++ -std=c++17 -Wall -Wextra -Werror -pedantic -fsanitize=address,undefined -fno-omit-frame-pointer`后运行alpha/beta。只声称本次无报告，没有推导所有生命周期安全；不为缺特定免责声明造partial。 |
| 2.1 | PRIVATE造成跨TU不同定义、ODR/ABI且可链接 | pass | A11–17说明PRIVATE只给packet.cpp而公开头布局受宏控制；A45说明相同符号可链接但较大写入破坏较小栈对象。虽未拼写ODR缩写，实质说明同类型跨TU定义不一致，不按关键词扣分。 |
| 2.2 | producer PUBLIC传递给未来链接消费者 | pass | W/2 `CMakeLists.txt:7` 唯一改动是PRIVATE→PUBLIC；8–9仍仅创建client并链接packet。A13–15解释传递使用要求。 |
| 2.3 | 无全局flags/逐client宏/packing/cast/布局改动 | pass | 最终四文件与原夹具对照：仅上述一行改变；`packet.hpp`、`packet.cpp`、`packet-client.cpp`逐字节相同。 |
| 2.4 | 检查双方编译命令、干净构建运行、sizeof不证ABI | pass | E674调用configure/build --verbose/run，E690含新构建目录配置及两条真实`/usr/bin/c++ -DPACKET_EXTENDED=1`命令，分别编译packet.cpp与packet-client.cpp，实际`client=16 library=16`；A47–57列偏移/顺序/条件成员/对齐/调用约定等sizeof未覆盖契约。 |
| 3.1 | 全atomic无race不等于跨对象发布正确 | pass | A5–9指出relaxed没有跨线程同步链、允许ready真后payload仍0；A45明确两对象均atomic，原协议可无TSan可报告race。 |
| 3.2 | ready release与观察该发布的acquire，payload relaxed | pass | W/3 `publication.cpp:14–21`只把ready两处改为release/acquire，payload两处保持relaxed；A15–25一致。 |
| 3.3 | SB/SW/HB链保证42，不靠join事后修复 | pass | A27–39明确store payload → SB → release → SW →读到true的acquire → SB → load payload，限定one-shot且不复位/再写。W/3:17–24 consumer创建仍在producer.join之前，未靠先join producer再启动consumer引入隐含HB。 |
| 3.4 | TSan检测race，阴性非atomic协议证明 | pass | A43–47区分三类工具覆盖与语言推理，不称原payload为非atomic race，也不承诺TSan必报。 |
| 3.5 | ASan+UBSan与TSan独立且本CPU实测不冒充可移植证明 | pass | E666有三个独立C++17/-pthread构建调用，优化、ASan+UBSan、TSan结果分别E674/E684/E679，均42；E775压力运行结果`10000 42`。A46–56明确硬件/调度覆盖有限，保证来自源级同步链。 |
| 4.1 | 不读cpp，路由Unreal或引擎文档 | pass | result的false与全场工具调用一致；E97/153/157/161及E191实读引擎文档，A370–376给Epic来源。 |
| 4.2 | 不以std::atomic/CMake替代引擎权限/预测 | pass | A3–8、83–117、135–182、201–217、286–325分别处理RPC发起端/所有权/相关性、复制条件、LocalPredicted和prediction key，无通用原子或构建替代。 |
| 5.1 | closure已销毁但Scheduler的frame仍在 | pass | A5准确区分捕获shared_ptr的闭包与惰性协程帧隐式对象引用；不是shared_ptr本身失效，而是owner仅在局部closure。 |
| 5.2 | owner按值进入真实跨suspension存储 | pass | W/5 `deferred-report.cpp:55–65`新增命名协程按值shared_ptr，submit移动到参数而非仅改lambda捕获；A22–33明确参数进入frame早于initial_suspend。submit返回时局部owner已移动并销毁，首次resume前frame仍有强引用。 |
| 5.3 | 保留lazy、move-only Task、Scheduler所有权及main检查 | pass | W/5:15–16仍suspend_always；21–31禁复制、移动handle、析构destroy；43–50仍Scheduler持有Task；68–83原main完全保留。最终修改只在原submit附近，没有同步执行、全局保留或泄漏closure。 |
| 5.4 | 未首次resume取消释放owner且不写，完成清frame也释放 | pass | A32–33说明两条路径；W/5:31/46/48分别destroy与clear，55–57输出仅在协程体；72–81检查排队存活、完成过期、取消前存活/后过期且输出仍daily。E517和E557运行这些真实检查成功。 |
| 5.5 | C++20现有检查实跑，显式过期失败不冒称sanitizer报告 | pass | E138/143为原文件C++20普通编译，E157/163运行明确`report expired while queued`、exit 1；修后E492/497普通编译、E511/517运行成功；E532/537以C++20 `-fsanitize=address,undefined -fno-omit-frame-pointer`独立编译，E551/557运行`completion and cancellation release reports`。A39–51没有把原显式weak_ptr检查当ASan诊断。 |

### 产物与实验边界

最终workspace逐文件与正式原夹具对照，只观察到四类必要源修复：
场景1删除view变量/头并改两次owning捕获；场景2一行PUBLIC；
场景3两处memory_order；场景5把捕获协程换为按值参数命名协程。
没有篡改alpha/beta、42、daily/discard输入、删除main检查、提前执行drain，
也没有改Task/Scheduler机制来过关。场景3的10,000次运行是多个独立程序，
没有向程序内部加入测试同步、sleep或新的重试；保留的yield轮询来自原夹具。
场景5现有main实际覆盖首次resume前保活和未resume取消，不扩大为任意外部awaiter、
运行中取消或跨线程调度证明。读取reference中的示例不计为编译过示例。

本轮审阅所有partial/fail：**无**。场景2缺ODR字样、场景1未另写全称免责声明
属于表达而非消费者故障；按原判据的语义评分，不以命名缺失制造收益或退化。

### 公共结构、安装及补充机制冒烟

以下为Main已执行并提供的公共验证事实，本审阅未重复运行：

- 五个正式skill各有4份一层references；cpp安装单元共15文件、恰好一个SKILL.md。
- `uv run tools/validate_skills.py`：60 skill(s)，0 errors / 0 warnings。
- `build_catalog --check`：current 60；五主题 `check_upstream` 共19条repo来源记录全up_to_date，
  `--pin`更新0。
- 隔离 `npx skills` 安装恰好5包，源与安装复制的所有文件逐字节一致，
  每包一个SKILL.md；不是只数入口、漏掉references或evals。
- 原25场定义和31夹具字节未改；原料已从research/evals迁至skills/topic/evals，
  cpp唯一有效评测入口是本节所链正式目录，不恢复旧副本。
- Main补充C++17 ASan+UBSan机制冒烟：普通构造异常 `member=1 owner=0`，
  委托构造异常 `member=1 owner=1`，one-shot输出42。这是已执行的机制检查，
  不是跨CPU发布证明，也不是全部协程路径验证，更不新增为第21项增益证据。

### 保持结论，不宣称D2增益通过

有skill **20/20 pass，0 partial，0 fail**，既有无skill **20/20**：
逐项差值0，五场均为保持，全部20项是本模型上的非区分项。四个正例正确导航、
负例在技能可用时拒绝读取，证明本轮路由和行为未观察到退化，
不证明正文修补了baseline遗漏。**D2“至少一个基线缺口被关闭”的增益门未通过**，
不能把安装成功、编译成功、较多工具调用或更长答案替代增益。
两批并非同时运行，且每配置每场单次；没有重复方差或其他模型数据，
也不从本次单模型结果外推跨模型稳定性。本轮交付完整skill内容及可复核保持证据，
按用户继续决定完成建设，不再重启知识题迫使差异；本审阅没有提交或推送。
