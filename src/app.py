import logging

import streamlit as st
import pandas as pd
from rich.logging import RichHandler


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[RichHandler(show_time=False, rich_tracebacks=True)]
)
logger = logging.getLogger(__name__)


def run_app():
    """ 講義アンケートの段階評価をカテゴリごとに集計・可視化するアプリ """
    logger.info("アプリを起動")

    # =============
    # ページ全体設定
    # =============
    st.set_page_config(
        page_title="講義アンケート集計ダッシュボード",
        page_icon=":speech_balloon:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    logger.info("ページ設定を適用")

    st.markdown(
        """
        <style>
        /* Metric をカード風に整形 */
        div[data-testid="metric-container"] {
            border: 1px solid rgba(49, 51, 63, 0.2);
            padding: 1rem 1rem 0.5rem 1rem;
            border-radius: 0.75rem;
            background-color: #FFFFFF;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        /* ラベル・値を中央寄せ */
        div[data-testid="metric-container"] > label,
        div[data-testid="metric-container"] > div {
            width: 100%;
            text-align: center;
        }
        
        /* タブヘッダのスタイル微調整 */
        [data-baseweb="tab"]:hover {
            background-color: rgba(0, 0, 0, 0.05);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    logger.info("共通CSSを設定")
    
    # ========
    # タイトル
    # ========
    st.title("📊 講義アンケート集計ダッシュボード")

    # ===============================
    # サイドバー：アップロード + ヘルプ
    # ===============================
    st.sidebar.header("⚙️ 操作メニュー")
    uploaded_file = st.sidebar.file_uploader(
        "CSVファイルをアップロード",
        type=["csv"],
        accept_multiple_files=False,
    )

    with st.sidebar.expander("使い方", expanded=False, icon="🗝️"):
        st.markdown(
            """
            1. Omnicampus から受講者アンケートを **CSV** 形式でエクスポートします。
            2. ここにアップロードすると自動でカテゴリ別に集計・可視化されます。
            """
        )

    # 未アップロードの場合は案内を表示
    if uploaded_file is None:
        logger.info("CSVファイルがアップロードされていません")
        st.info("👈 左のサイドバーから CSV ファイルをアップロードしてください")
        st.stop()

    # =============
    # データ読み込み
    # =============
    try:
        df = pd.read_csv(uploaded_file)
        logger.info("CSVファイルを読み込みました")
    except Exception:
        logger.exception("CSVファイルの読み込みに失敗")
        st.error("CSVファイルの読み込みに失敗しました")
        st.stop()

    st.success("✔️ CSVファイルを読み込みました")

    with st.expander("🔍 アップロードしたデータを確認 (先頭 5 行)"):
        st.dataframe(df.head(), use_container_width=True)

    # カテゴリと (ラベル, 質問) の定義
    categories = {
        "講義全体": [
            ("総合満足度", "本日の総合的な満足度を５段階で教えてください。 "),
            ("おすすめ度", "親しいご友人にこの講義の受講をお薦めしますか？"),
        ],
        "講義内容": [
            ("学習量", "本日の講義内容について５段階で教えてください。 \n学習量は適切だった"),
            ("理解度", "本日の講義内容について５段階で教えてください。 \n講義内容が十分に理解できた"),
            ("アナウンス", "本日の講義内容について５段階で教えてください。 \n運営側のアナウンスが適切だった"),
        ],
        "講師": [
            ("総合満足度", "本日の講師の総合的な満足度を５段階で教えてください。"),
            ("時間活用", "本日の講師について５段階で教えてください。\n授業時間を効率的に使っていた"),
            ("質問対応", "本日の講師について５段階で教えてください。\n質問に丁寧に対応してくれた"),
            ("話し方",   "本日の講師について５段階で教えてください。\n話し方や声の大きさが適切だった"),
        ],
        "自分自身": [
            ("予習", "ご自身について５段階で教えてください。\n事前に予習をした"),
            ("意欲", "ご自身について５段階で教えてください。\n意欲をもって講義に臨んだ"),
            ("今後の活用", "ご自身について５段階で教えてください。\n今回学んだことを学習や研究に生かせる"),
        ],
    }

    # 必須列チェック
    missing_cols = [
        full for qs in categories.values() for _, full in qs if full not in df.columns
    ]
    if missing_cols:
        logger.exception(f"以下のカラムが見つかりません: {missing_cols}")
        st.error("⚠️ 以下のカラムが見つかりません: " + ", ".join(missing_cols))
        st.stop()
    else:
        logger.info("全ての必要なカラムが存在します")

    # =======================
    # カテゴリ別にタブで可視化
    # =======================
    tabs = st.tabs(list(categories.keys()))

    for tab, (category_name, label_question) in zip(tabs, categories.items()):
        with tab:
            logger.info(f"「{category_name}」の集計を開始")
            
            labels = [label for label, _ in label_question]
            questions = [question for _, question in label_question]
            category_df = df[questions].apply(pd.to_numeric, errors="coerce")
            category_df.columns = labels

            mean_scores = category_df.mean()
            answer_counts = category_df.count()

            st.markdown(f"### {category_name} &nbsp;&nbsp;|&nbsp;&nbsp; **回答数: {int(answer_counts.mean())} 件**")
            st.divider()

            # 各設問を横並びのカード + 棒グラフで表示
            for label, question in zip(labels, questions):
                col_metric, col_chart = st.columns([1, 2], gap="small")

                # メトリックカード
                with col_metric:
                    st.metric(
                        label=label,
                        help=question,
                        value=f"{mean_scores[label]:.2f}",
                        border=True
                    )

                # 回答分布棒グラフ
                with col_chart:
                    counts = (
                        category_df[label]
                        .value_counts()
                        .reindex(range(1, int(category_df[label].max()) + 1))
                        .sort_index()
                    )
                    bar_df = pd.DataFrame({"評価": counts.index, "件数": counts.values}).set_index("評価")
                    st.bar_chart(bar_df, height=150, use_container_width=True)

                # セクション間の余白
                st.markdown("\n")

            logger.info(f"「{category_name}」の集計と可視化が完了")


if __name__ == "__main__":
    run_app()
