document.addEventListener('DOMContentLoaded', function () {
    const fileInput = document.getElementById('file-input');
    const fileNameDisplay = document.getElementById('file-name');
    const dropArea = document.getElementById('drop-area');

    // 處理檔案選擇
    fileInput.addEventListener('change', function() {
        const file = fileInput.files[0];
        if (file) {
            fileNameDisplay.textContent = file.name;
            fileNameDisplay.classList.add('active');  // **新增 active class**
        } else {
            fileNameDisplay.textContent = "Drop music files here, or click to select";
            fileNameDisplay.classList.remove('active');  // **移除 active class**
        }
    });

    // 監聽拖放區域的事件
    dropArea.addEventListener('dragover', function(event) {
        event.preventDefault();  // 防止默認行為（防止打開檔案）
        dropArea.classList.add('dragover');  // 當拖曳進來時改變背景顏色
    });

    dropArea.addEventListener('dragleave', function() {
        dropArea.classList.remove('dragover');  // 拖曳離開時移除背景顏色
    });

    dropArea.addEventListener('drop', function(event) {
        event.preventDefault();  // 防止默認行為（防止打開檔案）

        // 確認拖曳進來的是 .wav 檔案
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            const file = files[0];
            if (file.type === "audio/wav") {
                fileNameDisplay.textContent = file.name;  // 顯示檔案名稱
                fileNameDisplay.classList.add('active');  // 顯示 active class
                // 手動觸發 <input> 的 change 事件
                const dataTransfer = new DataTransfer();
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
            } else {
                fileNameDisplay.textContent = "Only .wav files are allowed";  // 只允許 .wav 檔案
                fileNameDisplay.classList.remove('active'); 
            }
        }
    });
});