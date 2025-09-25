# 如何使用 OpenBB Workspace 搭建A股和港股分析面板

openbb-hka 是一款基于 OpenBB Workspace 的应用，提供搭建A股与港股分析面板的模板与组件，数据源依托于 openbb-akshare 和 openbb-tushare。

在此之前，我已发布基于 AKShare 和 Tushare 的 OpenBB 数据源扩展。很多用户提出这样的疑问：为何要开发这些扩展？OpenBB 的核心价值是什么？我在《OpenBB 介绍及其在A股与港股金融数据分析中的应用》一文中尝试回应了这些问题，但真正理解 OpenBB 的设计理念，仍需结合实际使用体验。

另一个常见困惑是：OpenBB 是否具备前端界面？应如何使用？事实上，OpenBB Workspace 正是其前端实现。通过该平台，用户可搭建定制化的数据分析面板。针对特定市场（如A股和港股），我们能够开发专用的 OpenBB Workspace 应用，集成相关分析组件。openbb-hka 正是这样一个为构建A股和港股分析面板而设计的应用。

若希望从头开始搭建分析面板，可以使用 OpenBB Platform 作为后端。安装 OpenBB Platform 后，可通过运行 `openbb-api`命令启动自有后端服务。

下表对比了 OpenBB Workspace 应用与面板的主要特性：

| **应用（Apps）**             | **面板（Dashboards）**   |
| ---------------------------------- | ------------------------------ |
| 提供具备特定分析功能的预配置模板   | 支持自由配置的空白画布         |
| 组件已预置关联参数，开箱即用       | 需手动配置参数                 |
| 内置精选提示词库，提升分析效率     | 初始不包含预设提示，需自行构建 |
| 由领域专家设计，适用于特定工作流程 | 作为通用型分析工作空间使用     |

## 环境设置

在运行openbb-hka做为后端应用之前，需要设置所使用的数据源的API Key和一些环境变量。

### API Key 设置

虽然 AKShare 使用的是免费数据源，但在使用雪球数据时，仍需配置 API Key。请按如下方式在文件 `$HOME/.openbb_platform/user_settings.json`中设置 `akshare_api_key`：

```
{
    "credentials": {
        "akshare_api_key": "your {xq_a_token}"
    },
    "preferences": {},
    "defaults": {
        "commands": {}
    }
}
```

### 环境变量

除设置 API Key 外，部分配置需通过环境变量完成。请参考项目中的 `env.example`文件设置环境变量，或基于该文件生成你自己的 `.env`文件。

| 变量名称             | 说明                                    |
| -------------------- | --------------------------------------- |
| AGENT\_HOST\_URL     | 目前可留空                              |
| APP\_API\_KEY        | 可使用自行生成的 JWT Token 进行身份验证 |
| DATA\_FOLDER\_PATH   | 目前可留空                              |
| OPENROUTER\_API\_KEY | 目前可留空                              |
| FMP\_API\_KEY        | 目前可留空                              |

### 安装 `uv`

本项目使用 `uv`进行依赖管理。如系统中尚未安装，请先安装 `uv`。安装完成后，运行以下命令以同步环境：

```
uv sync
```

### 运行应用

通过以下命令启动应用：

```
uv run uvicorn main:app --reload
```

## 使用 Docker 部署

openbb-hka 支持通过 Docker 部署。

### 构建 Docker 镜像

使用以下命令构建 Docker 镜像：

```
docker build -t openbb-hka:0.2.4 .
```

使用此镜像前，需配置环境变量，相关变量存储于以下文件中：

* `.env`：请参照“环境设置”部分创建
* `user_settings.json`：请参考 OpenBB 官方文档进行配置

### 运行 Docker 镜像

可通过以下命令启动容器：

```
docker compose up
```

## 使用 Google Firebase Studio

如果不想在本地创建运行环境，openbb-hka 也可运行于 Google Firebase Studio 环境中。

<a href="https://idx.google.com/new?template=https://github.com/finanalyzer/idx/tree/main/hka">
  <picture>
    <source
      media="(prefers-color-scheme: dark)"
      srcset="https://cdn.idx.dev/btn/open_dark_32.svg">
    <source
      media="(prefers-color-scheme: light)"
      srcset="https://cdn.idx.dev/btn/open_light_32.svg">
    <img
      height="32"
      alt="Open in IDX"
      src="https://cdn.idx.dev/btn/open_purple_32.svg">
  </picture>
</a>

## 在 OpenBB Workspace 中使用 openbb-hka

您可以选择在本地运行 openbb-hka，或将其部署至云端环境。启动应用后，即可在 OpenBB Workspace 中添加并使用该应用。

![image01](https://raw.gitcode.com/FinAnalyzer/FinApp/files/master/docs/images/openbb_hka01.png)

如上图所示，点击 “Connect Backend” 按钮添加应用。添加成功后，Workspace 中将出现两个新应用：“A股”与“港股”。

点击“A股”应用，即可进入如下所示的分析面板界面：

![image02](https://raw.gitcode.com/FinAnalyzer/FinApp/files/master/docs/images/openbb_hka02.png)

目前面板包含三个主要部分：**简况**、**财务**与**股价**。您可以根据分析需求，自由添加、删除或调整控件，定制专属分析视图。

下图展示财务分析面板的示例界面：

![image03](https://raw.gitcode.com/FinAnalyzer/FinApp/files/master/docs/images/openbb_hka03.png)

以下为历史股价查询功能的界面示意图：

![image04](https://raw.gitcode.com/FinAnalyzer/FinApp/files/master/docs/images/openbb_hka04.png)

## AI 功能集成

OpenBB Workspace 中的所有分析控件均可添加至右侧的 Copilot 面板，用于执行智能分析。

## 总结


OpenBB Workspace 的组件与 Copilot 功能均支持基于需求的深度定制，用户可通过开发自有应用实现个性化扩展。

OpenBB 官方提供了以下应用开发模板以供参考：

* Backend 数据集成模板（[backends-for-openbb](https://github.com/OpenBB-finance/backends-for-openbb)）
* 自定义智能体模板（[agents-for-openbb](https://github.com/OpenBB-finance/agents-for-openbb)）

目前，openbb-hka 项目已基于 backends-for-openbb 模板完成初步开发。下一步将推进 Copilot 功能的本地化部署，届时中国区用户可在 OpenBB Workspace 中无缝接入千问、豆包等本地AI工具，进一步提升使用体验与操作效率。

