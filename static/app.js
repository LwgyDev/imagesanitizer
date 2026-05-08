//load from local storage
const settingsKeys = ['chk-strip-gps', 'chk-strip-device', 'chk-keep-copyright', 'chk-scramble-filename', 'sel-format'];
const savedSettings = JSON.parse(localStorage.getItem('sanitizerSettings') || '{}');
        
settingsKeys.forEach(id => {
    const el = document.getElementById(id);
    if (savedSettings[id] !== undefined) {
        if (el.type === 'checkbox') el.checked = savedSettings[id];
        else el.value = savedSettings[id];
    }
});

//save to local storage on change
document.querySelectorAll('.setting-input').forEach(el => {
    el.addEventListener('change', () => {
        const currentSettings = {};
        settingsKeys.forEach(id => {
            const input = document.getElementById(id);
            currentSettings[id] = input.type === 'checkbox' ? input.checked : input.value;
        });
        localStorage.setItem('sanitizerSettings', JSON.stringify(currentSettings));
    });
});

const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const uiLoading = document.getElementById('loading');
const uiResult = document.getElementById('result');
const uiError = document.getElementById('error-message');

['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, (e) => { e.preventDefault(); e.stopPropagation(); }, false);
});

['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-over'), false);
});

['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-over'), false);
});

dropZone.addEventListener('drop', (e) => { if(e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]); });
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', function() { if(this.files.length) handleFile(this.files[0]); });



async function handleFile(file) {
    uiResult.classList.add('hidden');
    uiError.classList.add('hidden');
    uiLoading.classList.remove('hidden')
    const formData = new FormData();
    formData.append("file", file);
    formData.append("strip_gps", document.getElementById('chk-strip-gps').checked);
    formData.append("strip_device", document.getElementById('chk-strip-device').checked);
    formData.append("keep_copyright", document.getElementById('chk-keep-copyright').checked);
    formData.append("scramble_filename", document.getElementById('chk-scramble-filename').checked);
    formData.append("output_format", document.getElementById('sel-format').value);

    try {
        const response = await fetch('/sanitize/', { method: 'POST', body: formData });

        if (!response.ok) {
            let errorMsg = "Server error occurred.";
            try {
                const errorData = await response.json();
                errorMsg = errorData.detail || errorMsg;
            } catch(parseErr) {
                errorMsg = await response.text(); 
            }
            throw new Error(errorMsg);
        }

           const imageBlob = await response.blob();
        const rawMeta = response.headers.get('X-Stripped-Metadata');
        const rawFilename = response.headers.get('X-Original-Filename');
                
        const strippedMetadata = rawMeta ? JSON.parse(decodeURIComponent(rawMeta)) : {};
        const originalFilename = rawFilename ? decodeURIComponent(rawFilename) : "image.jpg";

        const objectUrl = URL.createObjectURL(imageBlob);

        uiLoading.classList.add('hidden');
        uiResult.classList.remove('hidden');
                
        document.getElementById('download-btn').href = objectUrl;
        document.getElementById('download-btn').download = originalFilename;

        const metaTable = document.getElementById('metadata-table');
        metaTable.innerHTML = '';
        const metaKeys = Object.keys(strippedMetadata);
                
        if (metaKeys.length === 0) {
            document.getElementById('no-metadata').classList.remove('hidden');
        } else {
            document.getElementById('no-metadata').classList.add('hidden');
            metaKeys.forEach(key => {
                const tr = document.createElement('tr');
                const tdKey = document.createElement('td');
                tdKey.className = 'px-6 py-4 font-medium text-gray-900 bg-gray-50/50 border-r border-gray-100 w-1/3';
                tdKey.textContent = key;
                const tdVal = document.createElement('td');
                tdVal.className = 'px-6 py-4 break-all text-gray-700';
                tdVal.textContent = strippedMetadata[key]; 
                tr.appendChild(tdKey);
                tr.appendChild(tdVal);
                metaTable.appendChild(tr);
            });
        }
    } catch (err) {
        uiLoading.classList.add('hidden');
        document.getElementById('error-text').textContent = err.message;
        uiError.classList.remove('hidden');
    }
}