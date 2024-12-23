$(function () {
  //스크롤시 메뉴 상단고정
  $(window).scroll(function () {
    if ($(window).scrollTop() > 60) {
      $("#fs_header").addClass("active");
    } else {
      $("#fs_header").removeClass("active");
    }
  });

  $('#add-category').click(function() {
    add_category();
  })

  $(document).on('click', '.btn_del', function() {
    $(this).closest('.c_list').remove();
  });

  $('#upload').click(function(e) {
    e.preventDefault();
    const uploadButton = $(this); // upload button의 참조를 저장
    
    uploadButton.text('분류중'); // 버튼 텍스트를 '분류중'으로 변경
    uploadButton.prop('disabled', true); // 분류 시작 시 버튼 비활성화
  
    handleFormSubmit(e)
      .then(response => {
        if (response.ok) {
          uploadButton.text('분류완료'); // 'handleFormSubmit'이 완료되었을 때 '분류완료'로 변경
        } else {
          uploadButton.text('업로드 실패'); // 'handleFormSubmit'이 실패하면 '업로드 실패'로 변경
        }
      })
      .catch(err => {
        console.error(err); // 오류가 발생한 경우 콘솔에 오류 메시지 출력
        uploadButton.text('분류 완료'); // 오류가 발생한 경우 버튼 텍스트를 '오류 발생'으로 변경
      })
      .finally(() => {
        uploadButton.prop('disabled', false); // 분류 완료 후 버튼 활성화
      });
  });
  

  popupOpen();
});

function popupOpen() {
  //도움말 팝업
  $(".info_popup .btn_popup").on("click", function (event) {
    $("#pop_info").show(); //팝업 오픈
    $("body").append('<div class="backon"></div>'); //뒷배경 생성
    $("body").addClass("layer-open"); //overflow:hidden 추가

    $("body").on("click", function (event) {
      if (
        event.target.className == "btn_close" ||
        event.target.className == "backon"
      ) {
        $("#pop_info").hide(); //close버튼 이거나 뒷배경 클릭시 팝업 삭제
        $(".backon").hide();
        $("body").removeClass("layer-open");
      }
    });
  });

  //도움말 팝업
  $(".join_wrp .btn_info").on("click", function (event) {
    $("#pop_info_join").show(); //팝업 오픈
    $("body").append('<div class="backon"></div>'); //뒷배경 생성
    $("body").addClass("layer-open"); //overflow:hidden 추가

    $("body").on("click", function (event) {
      if (
        event.target.className == "btn_close" ||
        event.target.className == "backon"
      ) {
        $("#pop_info_join").hide(); //close버튼 이거나 뒷배경 클릭시 팝업 삭제
        $(".backon").hide();
        $("body").removeClass("layer-open");
      }
    });
  });
}

function add_category(category = '', description = '') {
  let category_num = $(".category_wrp .list_wrp .c_list").length;

  const categoryDiv = $('<div class="c_list list"></div>');
  const categoryItem = $(`<div class="list_item"></div>`);
  const descriptionItem = $(`<div class="list_item info"></div>`);

  const categoryInput = $(`<input type="text" placeholder="메인기술 입력" class="input_style" id="category${category_num+1}" name="categories" value="${category}">`);
  const descriptionInput = $(`<input type="text" placeholder="검색식 입력" class="input_style" id="cate_txt${category_num+1}" name="category_descriptions" value="${description}">`);
  const deleteButton = $('<button type="button" class="btn_del">X 삭제</button>');

  deleteButton.on('click', () => {
    categoryDiv.remove();
  });

  categoryItem.append(categoryInput);
  descriptionItem.append(descriptionInput);
  descriptionItem.append(deleteButton);

  categoryDiv.append(categoryItem);
  categoryDiv.append(descriptionItem);

  $(".category_wrp .list_wrp").append(categoryDiv);
}

$("#add-category").on('click', () => {
  add_category();
});


function loading() {
  //로딩중 화면
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

//monitorProgress();

function fileSelected() {
  const fileInput = document.getElementById('upload_file');
  const uploadStatus = document.getElementById('upload_status');

  if (fileInput.files.length > 0) {
    uploadStatus.textContent = '파일 첨부 완료';
  } else {
    uploadStatus.textContent = '파일 첨부';
  }
}


async function handleFormSubmit(e) {
  e.preventDefault();

  const apiKeyInput = document.querySelector('input[name="api_key"]');
  if (!apiKeyInput || !apiKeyInput.value.trim()) {
    alert('API 키를 추가해주세요');
    return; // API 키가 없으면 함수 실행을 중단
  }

  const categoryInputs = document.querySelectorAll('input[name="categories"]');
  const categoryDescriptionsInputs = document.querySelectorAll('input[name="category_descriptions"]');

  const categories = Array.from(categoryInputs).map(input => input.value);
  const categoryDescriptions = Array.from(categoryDescriptionsInputs).map(input => input.value);

  let formData = new FormData();

  let categoriesStr = categories.join("|");
  let categoryDescriptionsStr = categoryDescriptions.join("|");

  formData.append('categories', categoriesStr);
  formData.append('category_descriptions', categoryDescriptionsStr);
  formData.append('api_key', apiKeyInput.value); // API 키를 formData에 추가

  // 파일 추가 로직
  const fileInput = $("#upload_file");
  if (fileInput.length > 0 && fileInput.prop("files").length > 0) {
    formData.append('file', fileInput.prop("files")[0]);
  } else {
    alert('업로드할 파일을 선택해주세요.');
    return; // 파일이 없으면 함수 실행을 중단
  }

  // 파일 업로드 요청
  const response = await fetch('/upload', {
    method: 'POST',
    body: formData
  });

  // 응답 처리
  if (response.ok) {
    document.getElementById('upload-message').textContent = '파일 첨부 완료';
  } else {
    alert('파일 업로드에 실패했습니다. 다시 시도해주세요.');
  }

  return response;
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


function upload(formData) {
  $.ajax({
    url: "/upload",
    type: "POST",
    data: formData,
    processData: false,
    contentType: false,
    success: function (data) {
      console.log(data);
    },
    error: function (jqXHR, textStatus, errorThrown) {
      console.log(jqXHR);
      console.log(textStatus);
      console.log(errorThrown);
    },
  });
}

add_category(); // 초기 카테고리 추가