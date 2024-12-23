$(function () {
  // 스크롤시 메뉴 상단고정
  $(window).scroll(function () {
    if ($(window).scrollTop() > 60) {
      $("#fs_header").addClass("active");
    } else {
      $("#fs_header").removeClass("active");
    }
  });

  $('#upload').click(function(e) {
    e.preventDefault();
    const uploadButton = $(this); // upload button의 참조를 저장
    
    uploadButton.text('분류중'); // 버튼 텍스트를 '분류중'으로 변경
    uploadButton.prop('disabled', true); // 분류 시작 시 버튼 비활성화
  
    handleFormSubmit(e)
      .then(response => response.json())
      .then(data => {
        if (data.cancelled) {
          console.log('작업이 취소되었습니다.');
          window.location.href = '/'; // 첫 페이지로 리디렉션
        } else {
          uploadButton.text('분류 완료');
          console.log('작업이 완료되었습니다.');
          // 추가적인 완료 처리 로직
        }
      })
      .catch(err => {
        console.error('분류 완료:', err.message); // 오류 메시지 출력
        console.error('분류 완료:', err.stack); // 오류가 발생한 위치 출력
        uploadButton.text('분류 완료'); // 오류가 발생한 경우 버튼 텍스트를 '오류 발생'으로 변경
      })
      .finally(() => {
        uploadButton.prop('disabled', false); // 분류 완료 후 버튼 활성화
      });
  });

  popupOpen();
});

function popupOpen() {
  // 도움말 팝업
  $(".info_popup .btn_popup").on("click", function (event) {
    $("#pop_info").show(); // 팝업 오픈
    $("body").append('<div class="backon"></div>'); // 뒷배경 생성
    $("body").addClass("layer-open"); // overflow:hidden 추가

    $("body").on("click", function (event) {
      if (event.target.className == "btn_close" || event.target.className == "backon") {
        $("#pop_info").hide(); // close버튼 이거나 뒷배경 클릭시 팝업 삭제
        $(".backon").hide();
        $("body").removeClass("layer-open");
      }
    });
  });
}

// 취소 버튼 클릭 이벤트 바인딩
$('#cancel-upload').click(function() {
  cancelUploadProcess();
});

function cancelUploadProcess() {
  fetch('/cancel', { method: 'POST' })
  .then(response => response.json())
  .then(data => {
    console.log(data.message);
    resetUploadUI();
    window.location.href = '/'; // 첫 페이지로 리디렉션
  })
  .catch(error => console.error('Error:', error));
}

function resetUploadUI() {
  $('#upload').text('분류').prop('disabled', false);
  $('#upload_file').val('');
  $('#file-list').empty();
}

function loading() {
  // 로딩중 화면
  $("body").prepend(`
    <div id="loading_box">
      <div class="loading">
        <div></div>
        <div></div>
        <div></div>
        <div></div>
        <div></div>
      </div>
      <div class="l_txt">
        <p>데이터 처리중...</p>
        <p class="info">잠시만 기다려주세요.</p>
      </div>
    </div>
    <div class="loading_bg"></div>
  `);
}

function loading_end() {
  $("body").find("#loading_box").remove();
  $("body").find(".loading_bg").remove();
}

async function getProgress() {
  const response = await fetch('/progress');
  const progressData = await response.json();
  return progressData;
}

function updateProgress(progressValue) {
  // 진행 바를 갱신하는 코드
  $("#progress-bar").css("width", progressValue + "%");
}

function updateProgressStatus(status) {
  // 진행 상태를 갱신하는 코드
  $("#progress-status").text(status);
}

let timeoutId;

async function monitorProgress() {
  const progressData = await getProgress();
  updateProgress(progressData.value);
  updateProgressStatus(progressData.status);

  if (progressData.status !== '완료') {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return monitorProgress(); // recursive call
  } else {
    clearTimeout(timeoutId);
    // '완료' 상태가 반환되면 이 상태를 반환
    return progressData;
  }
}

async function handleFormSubmit(e) {
  e.preventDefault();

  const filenameInput = document.querySelector('input[name="filename"]');
  if (!filenameInput || !filenameInput.value.trim()) {
    alert('원하시는 파일 제목을 추가해주세요');
    return; // 파일 제목이 없으면 함수 실행을 중단
  }
  
  let formData = new FormData();

  // 파일 추가하는 코드
  const fileInput = $("#upload_file");
  if (fileInput.length > 0 && fileInput.prop("files") && fileInput.prop("files").length > 0) {
    formData.append('file', fileInput.prop("files")[0]);
  } else {
    alert('업로드할 파일을 선택해주세요.');
    return;
  }

  formData.append('filename', filenameInput.value); // API 키를 formData에 추가

  const response = await fetch('/upload', {
    method: 'POST',
    body: formData
  });

  if (response.ok) {
    document.getElementById('upload-message').textContent = '파일 첨부 완료';
  } else {
    alert('파일 업로드에 실패했습니다. 다시 시도해주세요.');
  }
  
  return response; // 이 부분을 추가했습니다.
}

$('#upload_file').on('change', function() {
  const fileList = $(this).prop('files');
  if (fileList.length > 0) {
    const file = fileList[0];
    $('#file-list').html(`
      <div class="c_list list">
        <div class="list_item info">
          <span class="file_name">${file.name} <em>(${(file.size / (1024 * 1024)).toFixed(1)}MB)</em></span>
          <button type="button" class="btn_del" onclick="clearFileInput()">X 삭제</button>
        </div>
      </div>
    `);
  } else {
    $('#file-list').empty();
  }
});

function clearFileInput() {
  $('#upload_file').val('');
  $('#file-list').empty();
}

document.addEventListener('DOMContentLoaded', function() {
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);
  socket.on('connect', function() {
      console.log('Websocket connected!');
  });

  var logElement = document.getElementById('realtime-log-container');
  var isScrollLocked = false; // 스크롤 잠금 상태 플래그
  var scrollThreshold = 70; // 맨 아래 범위 임계값 (px)

  function updateScroll(isForcedBottom) {
      if (isForcedBottom || !isScrollLocked && (logElement.scrollHeight - logElement.offsetHeight - logElement.scrollTop <= scrollThreshold)) {
          logElement.scrollTop = logElement.scrollHeight - logElement.offsetHeight;
      }
  }

  socket.on('log_update', function(msg) {
      var atBottom = logElement.scrollTop + logElement.offsetHeight >= logElement.scrollHeight - scrollThreshold;
      logElement.innerHTML += msg.data + '<br>';
      updateScroll(atBottom);
  });

  // 로그 컨테이너의 마우스 휠 이벤트 핸들러 추가
  logElement.addEventListener('wheel', function(event) {
      var delta = event.deltaY > 0 ? 50 : -50;
      logElement.scrollTop += delta;
      if (delta < 0) {
          isScrollLocked = false; // 스크롤을 올릴 때 자동 스크롤 잠금 해제
      } else {
          // 스크롤을 내릴 때만 잠금 상태를 재확인
          updateScroll(logElement.scrollTop + logElement.offsetHeight >= logElement.scrollHeight - scrollThreshold);
      }
      event.preventDefault();
  });

  // 로그 컨테이너 클릭 이벤트 핸들러 추가
  logElement.addEventListener('click', function() {
      isScrollLocked = !isScrollLocked; // 스크롤 잠금 상태 토글
      updateScroll(false);
  });
});

function fileSelected() {
  var file = document.getElementById('upload_file').files[0];
  if (file) {
    var selectedFileElement = document.getElementById('selected_file');
    selectedFileElement.querySelector('p').textContent = '업로드 파일: ' + file.name;
  }
  const fileInput = document.getElementById('upload_file');
  const uploadStatus = document.getElementById('upload_status');

  if (fileInput.files.length > 0) {
    uploadStatus.textContent = '파일 첨부 완료';
  } else {
    uploadStatus.textContent = '파일 첨부';
  }
}

// 파일 선택 취소 함수
function cancelUpload() {
  var input = document.getElementById('upload_file');
  input.value = ''; // 입력 초기화
  var selectedFileElement = document.getElementById('selected_file');
  selectedFileElement.querySelector('p').textContent = '파일이 비었습니다.';
}

// 취소 버튼 클릭 시 실행되는 함수
function cancelProcess() {
  fetch('/cancelProcess', { method: 'POST' })
  .then(response => {
      if (!response.ok) {
          throw new Error('Network response was not ok');
      }
      return response.json();
  })
  .then(data => {
      console.log(data.message);
      resetUploadUI();  // 업로드 관련 UI 초기화 함수 호출
      window.location.href = '/results';  // 첫 페이지로 리디렉션
      window.location.href = '/';  // 첫 페이지로 리디렉션
      if (window.location.pathname === '/') {
          window.location.reload();  // 이미 첫 페이지인 경우 강제로 새로 고침
      }
  })
  .catch(error => console.error('Error:', error));
}

add_category(); // 초기 카테고리 추가