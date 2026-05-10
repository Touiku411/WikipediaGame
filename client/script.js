const playBtn = document.getElementById('play-btn');
        const loading = document.getElementById('loading');
        const resultContainer = document.getElementById('result-container');

        playBtn.addEventListener('click', async () => {
            // 1. 改變按鈕狀態，顯示載入中
            playBtn.disabled = true;
            playBtn.innerText = "計算中...";
            loading.style.display = "block";
            resultContainer.style.display = "none"; // 隱藏上一次的結果

            try {
                // 2. 呼叫後端 API
                const response = await fetch('/find_path');
                const data = await response.json();

                // 3. 檢查是否有錯誤 (包含 Timeout 408 或 Server Error 500)
                if (!response.ok) {
                    alert(`挑戰失敗或超時：${data.error}\n\n但我們還是產生了題目：\n起點：${data.start_title}\n終點：${data.target_title}`);
                    return; // 結束執行
                }

                // 4. 把後端傳來的資料填入 HTML 裡面
                // 填入起點與終點
                const startLink = document.getElementById('res-start');
                startLink.innerText = data.start_title;
                startLink.href = data.start_url;

                const targetLink = document.getElementById('res-target');
                targetLink.innerText = data.target_title;
                targetLink.href = data.target_url;

                // 填入統計數據
                // ✅ 修正版寫法：先確保它是數字，再取小數點
                const safeTime = parseFloat(data.time) || 0;
                document.getElementById('res-time').innerText = `⏱️ 耗時: ${safeTime.toFixed(3)} 秒`;
                document.getElementById('res-discovered').innerText = `👁️ 探索頁面: ${data.discovered} 個`;
                document.getElementById('res-depth').innerText = `📏 總步數: ${data.path.length - 1} 步`;

                // 填入路徑清單 (把 URL 陣列轉成可點擊的 <li>)
                const pathList = document.getElementById('res-path');
                pathList.innerHTML = ""; // 清空上次的路徑
                data.path.forEach((url, index) => {
                    // 從網址把標題切出來顯示 (讓畫面比較好看)
                    const decodedTitle = decodeURIComponent(url.split('/').pop()).replace(/_/g, " ");
                    pathList.innerHTML += `<li><a href="${url}" target="_blank">${decodedTitle}</a></li>`;
                });

                // 5. 顯示結果區塊
                resultContainer.style.display = "block";

            } catch (error) {
                console.error("發生錯誤:", error);
                alert("伺服器連線發生問題，請確認後端有正常啟動！");
            } finally {
                // 6. 不管成功或失敗，最後都要把按鈕恢復原狀
                playBtn.disabled = false;
                playBtn.innerText = "🎲 再玩一次！";
                loading.style.display = "none";
            }
        });