# linux-ops 调研记录

> 正式正文与4份参考已完成，评测唯一入口为 [`skills/linux-ops/evals/`](../skills/linux-ops/evals/)。下文保留Phase A/B当时记录；用户继续建设后的最新结论见文末，内容交付不等于已证明增益。

## 调研日期与检索途径

- 调研及复核日期：2026-09-12。
- 范围：Linux 裸机/VPS 自托管的主机运维，category=platform。覆盖 systemd 生命周期、权限/capabilities、磁盘/inode/deleted-open、进程/FD、DNS/TLS/路由、主机防火墙、备份恢复与回滚。不覆盖云控制面、K8s 清单、纯应用代码诊断、专门 Shell 脚本开发。
- 从 web_search `linux systemd SKILL.md github skills` 发现 bagelhole、chaterm、HermeticOrmus、peterbamuhigire；已知 TerminalSkills 作为交叉源。搜索结果只用于发现，不用于评分。
- GitHub 数据全部通过登录的 `gh api repos/...`、`git/trees/<branch>?recursive=1`、`contents/<path>` 取得。首次 search/code 遇 EOF 和 timeout；随后已知仓库 API 成功，没有匿名 API 降级。五个目录树均 `truncated=false`。读取16份实际 SKILL.md 全文后评分；低分原文亦保留记录。
- 官方文档通过项目 manpages 阅读。read 的 ReadTheDocs 转换器曾自动跟随到 GitHub raw；为满足本批 GitHub 证据约束，Restic 和 Netplan 两份文档重新用 `gh api .../contents/...` 阅读校对，评分不依赖匿名 GitHub 页面。
- 本阶段没有执行主机命令、修改服务/防火墙、连接远程主机、测试、lint、安装或模型评测。

## 候选表

评分：权威/新鲜/具体/正确/许可；社区不是 Linux 官方。新鲜度按仓库 pushed_at，而不是声称技能正文最近更新；三月以前的 chaterm 超出六个月，强制 REJECT。INCLUDE 表示允许有选择地重写，不表示整份内容可无审查执行。

| # | 仓库/路径 | URL | Stars | 最近推送 | 许可 | 范围 | 权威 | 新鲜 | 具体 | 正确 | 许可分 | 总分 | 结论 | 理由 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | TerminalSkills/skills `skills/systemd` | [原文](https://github.com/TerminalSkills/skills/blob/56037efc04d0ffd20a0a85b18894115df74bd70f/skills/systemd/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 单元、timer、hardening | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE | enable/start 分离有用；Restart=always 普遍化不采用 |
| 2 | TerminalSkills/skills `skills/ssh` | [原文](https://github.com/TerminalSkills/skills/blob/56037efc04d0ffd20a0a85b18894115df74bd70f/skills/ssh/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 身份、跳板、转发 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 三项配置抽查通过；缺少安全切换门，不照抄硬化步骤 |
| 3 | bagelhole/devops-security-agent-skills `infrastructure/servers/linux-administration` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/infrastructure/servers/linux-administration/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | 主机综合 | 1 | 1 | 2 | 1 | 2 | 7 | MAYBE | inode 和进程定位可用；systemd-run 错称限制已运行进程 |
| 4 | 同仓 `infrastructure/servers/systemd-services` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/infrastructure/servers/systemd-services/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | notify/socket/resource | 1 | 1 | 3 | 0 | 2 | 7 | REJECT | OOMPolicy=continue 错称禁用OOM killer；StartLimit 放错节 |
| 5 | 同仓 `infrastructure/storage/backup-recovery` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/infrastructure/storage/backup-recovery/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | rsync/restic/restore | 1 | 1 | 2 | 1 | 2 | 7 | MAYBE | restore --target 有用；普通check错误称全数据检查 |
| 6 | 同仓 `security/network/firewall-config` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/security/network/firewall-config/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | iptables/nft/UFW | 1 | 1 | 2 | 0 | 2 | 6 | REJECT | 先flush/default drop后allow；UFW先enable后SSH，两个锁死路径 |
| 7 | 同仓 `security/network/ssl-tls-management` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/security/network/ssl-tls-management/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | certbot/OpenSSL/K8s | 1 | 1 | 2 | 1 | 2 | 7 | MAYBE | fullchain和SNI可用；无条件长期HSTS/preload不宜迁入 |
| 8 | 同仓 `security/hardening/linux-hardening` | [原文](https://github.com/bagelhole/devops-security-agent-skills/blob/0365f57a079b1332f95cf26e31dd2d5332a8399f/security/hardening/linux-hardening/SKILL.md) | 1084 | 2026-05-22T13:07:20Z | MIT | 权限/SSH/sysctl | 1 | 1 | 1 | 0 | 2 | 5 | REJECT | sysctl -p没有读取示例sysctl.d文件；默认drop早于SSH允许 |
| 9 | HermeticOrmus/linux-sysadmin-skills `skills/sysadmin-diagnose` | [原文](https://github.com/HermeticOrmus/linux-sysadmin-skills/blob/358769e5e43197609b093a354f182cc6ad1118c2/skills/sysadmin-diagnose/SKILL.md) | 3 | 2026-05-25T17:30:10Z | MIT | 假设驱动诊断 | 0 | 1 | 1 | 3 | 2 | 7 | MAYBE | 真实但主要是通用诊断清单，不作为权威运维内容 |
| 10 | 同仓 `skills/sysadmin-security` | [原文](https://github.com/HermeticOrmus/linux-sysadmin-skills/blob/358769e5e43197609b093a354f182cc6ad1118c2/skills/sysadmin-security/SKILL.md) | 3 | 2026-05-25T17:30:10Z | MIT | 交互审计 | 0 | 1 | 1 | 3 | 2 | 7 | MAYBE | 风险说明/确认先行；没有具体恢复程序，不抬高权威分 |
| 11 | peterbamuhigire/linux-skills `06-storage-and-filesystems/linux-disk-storage` | [原文](https://github.com/peterbamuhigire/linux-skills/blob/ee8c11527175708e2b2adab16bf3ee67496334b9/06-storage-and-filesystems/linux-disk-storage/SKILL.md) | 4 | 2026-09-07T10:33:25Z | frontmatter MIT，仓库无许可文件 | blocks/inodes/mounts | 0 | 3 | 3 | 1 | 1 | 8 | INCLUDE | 有明确观察/授权契约；references又称autoremove和旧tmp删除总是SAFE，必须裁掉 |
| 12 | 同仓 `03-networking-and-dns/linux-network-admin` | [原文](https://github.com/peterbamuhigire/linux-skills/blob/ee8c11527175708e2b2adab16bf3ee67496334b9/03-networking-and-dns/linux-network-admin/SKILL.md) | 4 | 2026-09-07T10:33:25Z | frontmatter MIT，仓库无许可文件 | route/DNS/Netplan/NM | 0 | 3 | 3 | 0 | 1 | 7 | REJECT | 以关网卡冒充rollback；将公网DNS与split-DNS差异直接判本地错误 |
| 13 | chaterm/terminal-skills `server/systemd` | [原文](https://github.com/chaterm/terminal-skills/blob/464c2954287ad0c0b9addb1ebfbb2150ddc0de24/server/systemd/SKILL.md) | 59 | 2026-03-03T03:28:35Z | Apache-2.0 | 服务/timer | 1 | 0 | 2 | 1 | 2 | 6 | REJECT | 超六个月；timer内联注释示例不可靠，frontmatter非规范 |
| 14 | TerminalSkills/skills `skills/restic` | [原文](https://github.com/TerminalSkills/skills/blob/56037efc04d0ffd20a0a85b18894115df74bd70f/skills/restic/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 备份/恢复 | 1 | 3 | 2 | 0 | 2 | 8 | REJECT | 声称init生成用户密码、管道备份atomic；脚本未检查dump失败 |
| 15 | 同仓 `skills/rsync` | [原文](https://github.com/TerminalSkills/skills/blob/56037efc04d0ffd20a0a85b18894115df74bd70f/skills/rsync/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 同步、增量、删除预览 | 1 | 3 | 2 | 3 | 2 | 11 | INCLUDE | 尾斜线/--delete/-n抽查通过；部署脚本失败处理不采用 |
| 16 | 同仓 `skills/iptables` | [原文](https://github.com/TerminalSkills/skills/blob/56037efc04d0ffd20a0a85b18894115df74bd70f/skills/iptables/SKILL.md) | 149 | 2026-09-04T19:42:42Z | Apache-2.0 | 主机过滤 | 1 | 3 | 2 | 1 | 2 | 9 | INCLUDE | 允许后drop优于候选6；缺IPv6必要控制流，不能整体迁入 |

## 深度审查

前六名为 #2、#15、#1、#16、#11 及并列7分中的 #5；六份已通读。API目录树核对：#1/#2/#15/#16/#5 均无同目录 references 可浏览；#11三个references真实存在且已浏览开头和相关章节，不把文中链接存在当作文件已读取。

1. **SSH (#2)**：四步示例短而可读，description有真实触发词，没有负边界。metadata.tags是列表，需扁平化且category改为platform。无Claude工具绑定。与systemd重叠在部署服务账户；只取ProxyJump、身份与转发目的端区分，不取“所有生产机立即关密码”和无条件Ed25519优越性的宣传句。缺少sshd语法验证、第二会话和回退，是后续基线要测的真实缺口。
2. **rsync (#15)**：正文紧凑，明确尾斜线与dry-run，适合做备份元数据差异入口。无agent绑定。metadata同上。脚本build失败仍继续同步、同步失败仍restart且没有已知好版本；不能保留。与#5重叠的传输步骤收敛为一个恢复验证流程，不把mirror当历史备份。
3. **systemd (#1)**：unit/timer/命令分离清楚，enable与start明确。通用Node示例和“timers更好”删去。Restart=always不能成为统一默认；启动类型与程序协议匹配应改从官方取证。无references，复杂capability和FD交互实际未覆盖。
4. **iptables (#16)**：顺序比#6安全，但允许已建立连接不是新登录验证；端口22假设、缺ICMPv6、没有回滚构成实质缺口。不能携带三个等价工具菜单；正文先识别已存在规则管理者，不另起UFW。无references或host变量依赖。
5. **disk-storage (#11)**：前半Required Inputs/Decision Rules精确，后半附带旧命令菜谱，存在明显自我冲突。metadata包含bool和list、作者电话等非必要载荷。跨skill/common.sh及仓库docs路径不能独立安装。浏览 `storage-reference.md`、`cleanup-patterns.md`、`cifs-and-network-mounts.md`：嵌套reference链接不合标准；cleanup对autoremove、旧tmp、邮件队列的SAFE/LOW分类过于冒进；后者仍解释deleted-open空间问题，可从unlink(2)独立取证，不迁脚本。
6. **backup-recovery (#5)**：备份/浏览/restore/retention组织完整，但一般check与read-data自相矛盾；复制运行中数据库目录、未先判活锁即unlock、latest跨主机都需要收紧。正文大量云与数据库代码越界，删除；无references。只作为恢复隔离目标的补充材料，不作为主干权威。

## 冲突与裁决

官方事实依据（已实读，版本敏感内容以目标机安装版本为准）：

- S1 [systemd.service(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)，页面systemd 261.2；Type=exec/notify、Restart、OOMPolicy。
- S2 [systemd.exec(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html)，页面systemd 261.2；AmbientCapabilities、NoNewPrivileges、LimitNOFILE、文件系统隔离。
- S3 [unlink(2)](https://man7.org/linux/man-pages/man2/unlink.2.html)，Linux man-pages 6.19；最后链接与最后FD关闭。
- S4 [path_resolution(7)](https://man7.org/linux/man-pages/man7/path_resolution.7.html)，Linux man-pages 6.19；逐级search权限与capabilities。
- S5 [nft(8)](https://netfilter.org/projects/nftables/manpage.html)；check、flush范围、inet涵盖两族、list ruleset可作为-f输入。
- S6 [iptables-apply(8)](https://man7.org/linux/man-pages/man8/iptables-apply.8.html)，iptables 1.8.13；超时回滚，IPv6对应工具。
- S7 [OpenSSH ssh_config(5)](https://man.openbsd.org/ssh_config)，IdentityFile、ProxyJump、LocalForward。
- S8 [rsync(1)](https://download.samba.org/pub/rsync/rsync.1)，尾斜线、--delete、-n、-a与-HAX的边界。
- S9 [Restic repository checking](https://restic.readthedocs.io/en/stable/045_working_with_repos.html)，gh实读 `restic/restic:doc/045_working_with_repos.rst`；check只检查结构，read-data读取payload。
- S10 [Netplan try](https://netplan.readthedocs.io/en/stable/netplan-try/)，gh实读 `canonical/netplan:doc/netplan-try.md`；120s默认及回滚已知问题。
- S11 [systemctl(1)](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)；runtime status、unit磁盘内容与manager状态、enable/start。
- S12 [sysctl(8)](https://man7.org/linux/man-pages/man8/sysctl.8.html)；-p默认只读/etc/sysctl.conf。
- S13 [systemd.syntax(7)](https://www.freedesktop.org/software/systemd/man/latest/systemd.syntax.html)；只有行首#或;为注释。
- S14 [NGINX HTTPS](https://nginx.org/en/docs/http/configuring_https_servers.html)；证书链与SNI。

| 冲突点 | 上游主张 | 裁决 | 依据 |
|---|---|---|---|
| 重启策略 | #1统一always；#4 on-failure但OOM解释错 | 按服务退出语义决定，长运行默认on-failure；OOMPolicy=continue不是禁止kernel杀进程 | S1 |
| Capability授予 | #1空缺；#4以名单呈现 | bounding只限上界；检查NNP/file/ambient交互，不能为bind错误改root | S2/S4 |
| disk已删仍满 | #3直接clear logs；#11前半诊断后半truncate | 先按设备+inode去重deleted-open，处理全部持有者；单独检查inode；不默认proc-FD截断 | S3 |
| 防火墙变更 | #6先drop；#16先allow但只验证现有session | 保存运行态和持久态、先武装脱离SSH的超时回滚；新会话+业务证据后撤销；识别IPv6 | S5/S6 |
| 网络rollback | #12给关接口的timeout命令 | 关接口不是恢复先前配置；Netplan try也需要核对实际回滚和磁盘配置 | S10 |
| 备份完整性 | #5普通check全数据；#14管道天然atomic | 区分结构完整、payload完整、应用一致和恢复演练；保留失败状态，不因snapshot存在宣告恢复可用 | S9 |
| 同步元数据 | #15-a示例；用户可能需ACL/xattr/hardlink | -a不含-HAX；按恢复目标显式保留并实测属性，--delete镜像不替代版本历史 | S8 |
| 权限 | #8固定chmod模板 | 依据主体、祖先目录search、ACL、MAC与service namespace分别判定，拒绝chmod777或取消hardening兜底 | S2/S4 |

### 正确性三点抽查记录

抽查通过不等于全文认证；发现的额外安全缺陷仍记录并禁止迁入。

| 候选 | 三点抽查（通过/错误） | 依据 |
|---|---|---|
| #1 | enable非start通过；oneshot timer搭配通过；always通用默认错误 | S1，systemctl语义 |
| #2 | IdentityFile通过；ProxyJump通过；本地转发目标从远端连接通过 | S7 |
| #3 | df/du不同测量对象通过；inode独立通过；systemd-run限制已运行进程错误（实际启动新命令） | S3；S1中systemd-run定义 |
| #4 | notify要求READY通过；StartLimit放Service错误；OOMPolicy禁OOM错误 | S1 |
| #5 | restore隔离target通过；check --read-data通过；check全payload错误 | S9 |
| #6 | inet两族通过；先drop后管理allow错误；UFW先enable后SSH错误 | S5/S6 |
| #7 | SNI选择名字通过；服务端fullchain而非leaf通过；未经子域盘点强制长期includeSubDomains/preload错误 | TLS服务端证书链机制；该候选不作为主干 |
| #8 | 最小权限目标通过；sysctl -p默认路径与示例不符错误；先drop后allow错误 | S4/S6/S12 |
| #9 | status是状态通过；journal按unit取证通过；重现原症状验证通过 | S1 |
| #10 | 权限审计通过；监听与规则分开通过；恢复演练必要通过 | S4/S5/S9；没有具体性则只给1分 |
| #11 | deleted-open通过；inode与blocks独立通过；旧tmp/自动卸包总是SAFE错误 | S3/S4；删除授权与运行中引用不可由mtime推知 |
| #12 | Netplan try超时通过；关闭interface恢复旧配置错误；公网与本地DNS不同必为错错误 | S10；split-DNS允许多视图 |
| #13 | enable/start分离通过；unit优先路径通过；timer值后内联注释错误 | S11/S13；超期直接排除不再迁入 |
| #14 | restore --target通过；init自动生成用户密码错误；dump管道atomic错误 | S9；上游原文管道未检查producer状态 |
| #15 | source尾斜线通过；--delete删除接收端多余项通过；-n预览通过 | S8 |
| #16 | established规则通过；inet两族通过；示例IPv6默认drop又不放必要控制流错误 | S5/S6 |

## 最终合入清单

**Phase A/B立项门通过，但不是正式技能完成。** 16个候选，5个活跃且≥8分INCLUDE（#1/#2/#11/#15/#16），6个REJECT，5个MAYBE。三个已明确开源、可独立计数的技能 #1/#2/#15 来自同一仓库；本仓标准允许同仓不同skill算候选，未把它们假称三个独立维护团队。另有#16与#11补充。没有Linux官方组织skill，不援引官方例外。上游数量满足形式门槛，权威/深度仍靠官方手册校正；不把通用DevOps清单当权威。

| id | 上游 | relation（Phase C拟定） | 贡献 |
|---|---|---|---|
| terminal-ops | TerminalSkills/skills，main @ 56037efc04d0ffd20a0a85b18894115df74bd70f，skills/systemd、skills/ssh、skills/rsync | merged | Service lifecycle, SSH path selection, and synchronization semantics, rewritten after baseline evidence. |
| terminal-firewall | 同repo/ref/commit，skills/iptables | reference | Firewall coverage checklist; all adopted facts rederived from nft/iptables manuals. |
| peter-storage | peterbamuhigire/linux-skills，main @ ee8c11527175708e2b2adab16bf3ee67496334b9，06-storage-and-filesystems/linux-disk-storage | reference | Deleted-open and inode coverage; no unsafe cleanup recipes or script dependency copied. |
| bagel-backup | bagelhole/devops-security-agent-skills，main @ 0365f57a079b1332f95cf26e31dd2d5332a8399f，infrastructure/storage/backup-recovery | reference | Isolated restoration workflow comparison only. |
| linux-manuals | S1–S14 | reference | Normative semantics; no manual prose copied. |

许可：TerminalSkills API Apache-2.0、bagelhole/Hermetic MIT、chaterm Apache-2.0。peter API license=null，完整目录树无LICENSE，README未给出许可文件；只有frontmatter MIT，许可分1，保守仅reference。没有GPL/专有文本进入merged。官方文档本阶段仅reference，不冒称MIT；未来SOURCES逐条记录真实许可。

## 基线缺口

**Main已实跑首轮1–5及追加6，无实质缺口：21/21项满足。** 模型为 `openai/gpt-5.6-sol`，thinking=`medium`；六份result.json均status=ok、skill_read=false。作者逐份阅读全文并按既有预期评分，不为少一个措辞或未指定备用工具判失败。临时Scope/SOURCES骨架已移出安装目录；不能发布或声称技能有增益。

| 场景 | 待观察行为 | 夹具及安全性 |
|---|---|---|
| 1 service privilege/FD | NNP/file/ambient交互，select软FD上限，reload与activation不同 | service-incident.txt；只读合成现场 |
| 2 blocks+inodes | 两个FD同inode不双算、最后holder、inode独立压力、拒盲删 | capacity-incident.txt；只读合成现场 |
| 3 remote firewall+TLS | established掩盖新SSH失效、2222/IPv6保留、持久与运行态回滚、IPv6证书错误 | network-change.txt；文档保留地址，无网络连接 |
| 4 restore | 跨host latest、26小时RPO不达标、未测RTO、-a缺HAX、恢复隔离/写入协调 | restore-evidence.txt；只读合成现场 |
| 5 near-miss | Linux运行环境不应吸走Python名称绑定问题 | 无夹具，不应读取linux-ops |
| 6 namespace renewal | 主进程单文件bind固定旧inode；ExecReload独立namespace读到新文件；绑定列表叠加与稳定目录内原子更新 | tls-namespace-renewal.txt；只读合成现场，基线4/4 |

夹具现保存在 `research/evals/linux-ops/files/`，均英文、小于50KB；恢复到skill目录后`files`位于evals/files，query只用basename符合runner扁平复制。所有查询明确分析而不操作宿主机；没有可执行脚本、sudo、真实凭证、远程主机或隐含工具成功标准。场景测具体裁决，不要求固定措辞或万能清单。复杂交互主要在1/2/3/4/6。

## 评测结果

| 场景 | 模型 | 有/无skill | skill_read | 达成项 | 备注 |
|---|---|---|---|---|---|
| 1 | openai/gpt-5.6-sol / medium | 无 | false | 3/3 | answer.md:9–27能力机制；42–88保持加固、激活与健康；90–100拒绝select高FD |
| 2 | openai/gpt-5.6-sol / medium | 无 | false | 4/4 | answer.md:5–15去重与双重压力；19–38拒绝破坏；61–85先保留日志再USR1、独立inode治理 |
| 3 | openai/gpt-5.6-sol / medium | 无 | false | 4/4 | answer.md:5–28新连接/IPv6/锁死；63–99双态回滚与脱离SSH/跨重启；103–113定位IPv6 TLS |
| 4 | openai/gpt-5.6-sol / medium | 无 | false | 4/4 | answer.md:7–25 RPO/RTO/check；39–71 latest/镜像；108–174隔离恢复、HAX、增量与回退 |
| 5 | openai/gpt-5.6-sol / medium | 无 | false | 2/2 | result.json:8未读技能；answer.md:1–38正确解释绑定与原地clear |
| 6 | openai/gpt-5.6-sol / medium | 无 | false | 4/4 | answer.md:5–49解释inode/namespace并拒两种兜底；54–89重置绑定、排空重启；93–154未来reload及主进程/新连接证据 |

证据目录：`/tmp/hs-five-20260912/evals/linux-ops/openai-gpt-5.6-sol-medium/baseline/{1..6}/`，每场景含answer.md、events.jsonl、result.json。表内行号均指对应编号的answer.md；skill_read取runner事件归纳的result.json。作者未再次调用模型。

### 保留首轮并追加场景6的理由

首轮所有预期已由模型自发满足，属于非区分项，不能支撑正文。场景2甚至识别关闭最后FD之前应保留七天日志；场景4额外处理跨目录硬链接与两次增量切换。保留原场景用于防回归，不人为降低它们的分数。

场景6来自真实systemd/内核主机边界：`BindReadOnlyPaths`单文件挂载持有旧对象，renewal以rename替换路径；新ExecReload进程拥有重新构建的mount namespace，却给旧namespace中的MainPID发信号，因此helper新序列号与主进程旧序列号同时正确。S2的BindPaths与PrivateMounts章节明确独立namespace及追加/空值重置语义，S3说明去掉旧名字不等于对象失效。夹具给出rename方式、两个inode、mountinfo、reload协议和可接受的一次drain，不藏关键需求。

预期包括定位上述交互、拒绝daemon-reload或proc-root覆盖兜底、切换稳定父目录只读bind并清掉旧file-bind列表、一次受控drain/restart后未来reload-only续期及真实客户端验证。允许其他同样具体且满足隔离/可用性的设计，不按某句固定命令评分。只有该基线出现实质失败，才进入Phase C。

追加结果：场景6的4项全部达成，累计21/21。模型没有误把helper看到的新证书当成主进程已加载，显式清空旧绑定列表，保留只读与非root隔离，并覆盖长连接排空、串行化发布和新SNI握手验证。没有运行宿主机服务或真实网络变更。当前未形成可证明的技能增益，保留为构建准备，不发布scope骨架。

## 备注

Phase C的拟建范围是一个主机变更/诊断工作流，reference只在基线实际遗漏对应规则时创建：service-privileges-and-limits、storage-and-processes、network-and-remote-changes、backup-and-restore。不能按菜单预先填满正文。Main提供逐项基线结果后再决定写哪些规则；全部通过则先调整场景，不空造增益。本子任务没有格式化、lint、测试、模型评测、安装冒烟、生成目录修改或commit/push。

## Phase B构建准备交付（历史记录）

当时只保留评测和只读现场，不向安装目录加入空skill。原6场景与5份现场夹具现已原样迁入[正式评测目录](../skills/linux-ops/evals/)，不再维护准备目录副本或骨架恢复命令。用户随后要求正式建设，按[路线图](../docs/roadmap.md)使用同模型medium与独立输出进行对照；没有把场景分析授权扩展成主机操作授权。

## Phase C 正式构建（用户明确继续）

2026-09-12，用户在获知上一轮仅完成 Phase B、没有技能正文之后明确要求“好，正式开始构建skill”。本轮按此新决定完成正文建设，不再把先证明强基线缺口作为停笔条件；这不推翻上面的历史实验。现有六场景仍为无 skill 21/21，全部是当前模型上的非区分项。**正文已经写成，不等于已证明增益；with-skill 与发布校验待 Main 统一执行。**

### 实际交付结构

- `skills/linux-ops/SKILL.md`：platform，2026.09.12，限定裸机/VPS主机边界；16条核心规则；诊断、服务变更、容量恢复、远程访问变更、备份恢复五条带具名验收门的工作流。正文要求观察/计划/授权执行分开，分析夹具不会自动变成真实主机连接或修改。
- `references/service-privileges-and-limits.md`：磁盘配置/manager配置/活进程三态；exec/notify/reload协议；非root、祖先search、ACL/MAC、bounding/ambient/NNP；single-file bind旧inode、ExecReload独立namespace、绑定列表整体重置及保留其他bind；稳定父目录与受控drain/restart迁移；select与FD软上限、user manager hard limit及cgroup区别。
- `references/storage-and-processes.md`：blocks/inodes/quota/read-only/FD不同资源；按device+inode汇总deleted-open全部holder；先保留证据再释放最后引用；不把proc-FD截断、盲删tmp或kill当修复；目标确认、外部恢复与剩余写入证据。
- `references/network-and-remote-changes.md`：resolver/NSS与split-DNS、路由/监听/过滤分层；sshd -t/-T Match检查；关闭multiplexing的新SSH连接；双栈规则、独立回滚执行器、运行态+持久态、回滚重放不能简单叠加；逐A/AAAA端点SNI/链验证。
- `references/backup-and-restore.md`：RPO实际可恢复点、全链路RTO、普通check/payload check/应用一致/实际restore四种证据；显式snapshot ID与--path不是内容过滤；隔离目标、非root检查、元数据与HAX、writer fence/final delta、接受新写后不能盲切回旧树。
- `SOURCES.yaml`：三个TerminalSkills独立skill分开列merged，明确同仓而非独立团队；其余官方资料均reference，无GPL/LGPL/CC-BY-SA原文或代码复制。未新增脚本。
- 原 `research/evals/linux-ops/` 用不转换内容的目录复制恢复到 `skills/linux-ops/evals/`，六个定义及五份原错误夹具保持原内容；旧路径最终归档移除交给Main，作者未删除历史证据。

### 本轮实读来源与落点

本轮没有重搜16候选，更没有泛搜五主题75候选；通过已登录 `gh api` 解析TerminalSkills main HEAD为 `56037efc04d0ffd20a0a85b18894115df74bd70f`，重新实读 `skills/systemd/SKILL.md`、`skills/ssh/SKILL.md`、`skills/rsync/SKILL.md` 全文与LICENSE元数据（Apache-2.0）。分别贡献服务组织、SSH连接路径和rsync同步语义；拒绝全局Restart=always、无条件关闭密码和失败后继续部署脚本。

官方校正本轮实读：

| 来源id | 实读内容 | 正文落点 / 许可 |
|---|---|---|
| systemd-exec | 261.2 BindPaths、NNP、bounding/ambient、rlimits、PrivateMounts原文段落 | service/storage/network；LGPL-2.1-or-later，API读取man/systemd.exec.xml SPDX确认 |
| systemd-service | Type、ExecReload、Restart、OOMPolicy段落 | service；LGPL-2.1-or-later，仅事实reference |
| systemctl-manual | cat/show、enable、reload、daemon-reload | 主文及service三态；LGPL-2.1-or-later |
| linux-unlink / linux-path | Linux man-pages 6.19 unlink与path_resolution原文 | storage/service；Linux-man-pages-copyleft，另通过API读取历史源文件许可头，不把历史源版本当本轮事实版本 |
| openssh-sshd | 官方sshd(8) -t/-T/-C、端口覆盖与reload | network；SSH-OpenSSH，API实读sshd.8的Ylonen及BSD二条款许可头 |
| nft-manual | nft(8) check、family、ruleset序列化与版权段落 | network；文档明确CC-BY-SA-4.0，不误写程序GPL-2.0许可 |
| nginx-tls | configuring_https_servers链顺序、缓存中间证书、SNI握手 | network；通过nginx/nginx.org LICENSE确认BSD-2-Clause |
| rsync-manual | archive遗漏HAX、尾斜线、dry-run、hardlink、transport与COPYING | backup；GPL-3.0-or-later，仅事实reference，COPYING还列linking exceptions |
| restic-docs | master HEAD `ba802d42b7294c98b62c16d1157ea3e80820c019`，完整045_working_with_repos.rst与050_restore.rst | backup；API确认BSD-2-Clause，明确check不是全payload或应用恢复证明 |

前轮peter来源依旧维持许可不明、仅reference裁决；本轮没有采用其文本或脚本，也没有重新读取后冒称合入，故正式SOURCES仅列本轮实际使用的资料。bagel与Terminal iptables同样留在历史候选/冲突表，不为凑数量进入本次SOURCES。netfilter git COPYING请求遇到反机器人页面，随后直接读已获取nft手册的版权段落得到文档CC-BY-SA-4.0；没有绕过验证或将挑战页当源文。

### 状态与未运行事项

本轮只完成资料实读、正文/溯源写入和既有eval文件复制。遵守并行约束，**没有运行格式化、lint、测试、构建、安装冒烟、模型评测、全库校验或check_upstream --pin**，没有连接真实主机、执行主机变更、修改其他skill/生成物，也没有提交或推送。上述验收门是技能消费者未来的执行要求，不是作者本轮执行成功的声明。Main将统一进行with-skill、结构/引用/安装验证与最终集成；不能根据正文存在宣称21/21基线获得提升。

## Phase D 统一验证与实际行为对照（2026-09-12）

Main 已完成上节交接后的统一审阅、安装、结构检查和原6场 with-skill。
原定义及5份夹具逐字节迁入
[正式评测目录](../skills/linux-ops/evals/)，没有把运维方案写回原始证据。
固定 `openai/gpt-5.6-sol`、`--thinking medium`；实际 assistant 消息也核对为该模型。

令 `R=/tmp/hs-five-build-20260912/evals/linux-ops/openai-gpt-5.6-sol-medium/skill`。
下文 `N/A`、`N/E` 指 `R/N/answer.md`、`R/N/events.jsonl`。
旧基线在 `/tmp/hs-five-20260912/evals/linux-ops/openai-gpt-5.6-sol-medium/baseline/`。
这些都是只读诊断/方案场景；事件中没有 bash、exec 或 OneSSH 主机变更调用。
**可执行方案判据通过，不等于执行过重启、防火墙切换、证书轮转或恢复演练。**

| 场景 | 秒 | 读取本 skill | pass / partial / fail |
|---|---:|---|---|
| 1 capability 与 select FD 上限 | 129.6 | 是 | 3 / 0 / 0 |
| 2 deleted-open 与独立 inode 压力 | 211.9 | 是 | 4 / 0 / 0 |
| 3 防火墙回退与 IPv6 TLS | 176.5 | 是 | 4 / 0 / 0 |
| 4 异机快照、RPO 与恢复发布 | 203.7 | 是 | 4 / 0 / 0 |
| 5 Python 名称重绑定近似负例 | 28.1 | 否 | 2 / 0 / 0 |
| 6 单文件 bind mount 与证书轮转 | 143.4 | 是 | 4 / 0 / 0 |

### 原21条判据与证据

| 原判据 | 裁决 | 答案证据及判读 |
|---|---|---|
| 1.E1 capability 授予机制 | pass | 1/A:5–50；bounding set 只是上限，NNP阻止exec从filecap取新权限，恢复特定 ambient CAP_NET_BIND_SERVICE，不改root、不关闭NNP |
| 1.E2 保留隔离并验证真实服务 | pass | 1/A:40–115；保留ledger写目录和文件系统限制，unit verify、daemon-reload、授权restart之后核对实际PID capability与新客户端端口/应用健康 |
| 1.E3 select 的 FD_SETSIZE | pass | 1/A:138–155；拒绝把soft NOFILE一律升过1024，不以更大rlimit取代后端适配 |
| 2.E1 一个70GiB inode的所有持有者 | pass | 2/A:13–22、87–95；相同device/inode两FD不相加成140GiB，所有holder释放后才真正回收 |
| 2.E2 inode与块压力分别处理 | pass | 2/A:28–35、100–126；关大文件不释放数百万staging inode，分别复查df块与inode |
| 2.E3 拒绝破坏性解法与正确reopen | pass | 2/A:39–58、75–95；拒绝重复unlink/proc-FD截断及未授权删除，用文档SIGUSR1覆盖全部相关worker或授权优雅restart，再检查健康 |
| 2.E4 留存与staging用途 | pass | 2/A:75–83、100–115；先外部保存七天日志，staging用途/保留策略确认后才讨论清理，不把磁盘紧张当删除权限 |
| 3.E1 旧SSH连接不是新会话证明 | pass | 3/A:7–28；2222未放行会阻断新连接，既有ESTABLISHED下whoami不能证明新规则安全 |
| 3.E2 真实管理源与双栈控制流 | pass | 3/A:46–76；候选保留真实管理源/2222与必要ICMPv6，不替换成22或只写IPv4规则 |
| 3.E3 激活前武装脱离会话的回退 | pass | 3/A:89–134；先验证定时回退恢复运行态和持久文件，再激活候选，以新SSH和服务连通为取消回退条件 |
| 3.E4 IPv6 SNI证书而非DNS | pass | 3/A:142–169；定位IPv6 TLS端点wrong certificate/vhost，不curl -k、不清空规则或删除应保留的AAAA |
| 4.E1 显式本机快照与隔离恢复 | pass | 4/A:7–16、62–93；拒绝latest取到other-vps，明确files-vps/1111aaaa并恢复隔离目录而非覆盖根 |
| 4.E2 删除传播与元数据 | pass | 4/A:12、49–58、99–108；解释--delete镜像传播删除，archive漏HAX，要求权限及hardlink/ACL/xattr核对 |
| 4.E3 三种备份验证与未测RTO | pass | 4/A:31–43、79–108；结构check、read-data与应用恢复演练分开，不宣称两小时RTO已实测 |
| 4.E4 RPO、当前写入及回退 | pass | 4/A:17–29、124–164；26小时超过24小时RPO，保留快照/current uploads、发布前write barrier/delta、旧代回退和延后prune |
| 5.E1 Python负例不读取运维 | pass | 5/result.json skill_read=false；事件无本 skill/参考读取 |
| 5.E2 重绑定与共享对象修改 | pass | 5/A:1–38；解释局部cache={}与cache.clear()区别，不提systemctl、防火墙或主机重启 |
| 6.E1 路径替换与不同mount namespace | pass | 6/A:5–18；主进程旧单文件bind钉旧inode，ExecReload新namespace可见1002，不把helper成功当主进程换证成功 |
| 6.E2 不以reload重建namespace或越过只读 | pass | 6/A:24–47；daemon-reload+HUP不更新主进程bind，不写/proc-root来绕过隔离或暴露半对证书 |
| 6.E3 替换而非叠加单文件bind | pass | 6/A:57–71；清空两条继承file bind，改稳定专用父目录只读bind，保留其他hardening |
| 6.E4 一次授权重启及未来无重启轮转 | pass | 6/A:79–179；先drain/restart实例化namespace，以锁串行发布匹配pair；核主进程实际视图/serial、新SNI握手、长流和回退pair，后续reload保持MainPID |

实际参考导航：1读service-privileges-and-limits，2读storage-and-processes，
3读network-and-remote-changes，4读backup-and-restore，
6读service与network；负例不读。四份参考都由对应正例真实打开。

### 附加表述缺陷与验证边界

场景4答案137–139把“旧树改名保留，再把新树改名到活动路径”的两次rename整体
称为原子切换。这不是一个原子交换，读者可能遇到路径空窗。
该答案的写屏障、delta和旧代回退满足原4.E4，但**不能当作零间隙读访问保证**。
原判据没有零读中断要求，故不临时新增隐藏扣分项；错误附加措辞在此明确保留。
已审阅的 backup-and-restore 参考131–148要求写屏障、流量协调和回退，
没有作“两次rename整体原子”的错误承诺，不以评测答案的附加措辞反写正确规则。

五主题合并工作区统一校验60 skill、0 error/0 warning，目录 current 60；
19条仓库型来源记录全部 up_to_date，pin更新0。隔离安装恰好五包，
linux-ops 的13个文件与源逐字节一致，每包只含一个 SKILL.md。
模型和 Main 本轮均未连接授权主机或执行生产运维；安装/文本检查不证明RTO、
RPO达标、真实网络回退或证书轮转无中断。

### 结论

原判据本轮21/21 pass、基线21/21，逐项增益0，都是指定强模型上的非区分项。
D2“至少关闭一个基线缺口”的增益门未通过；不把更长方案、正确导航或安装完成
冒充净提升。按用户获知基线后仍明确继续的决定交付完整skill，
保留原场景和上面的附加缺陷，不再追加知识题迫使差异。
每配置每场单次运行，不外推跨模型、重复运行稳定性或真实主机操作结果。
