$(function(){
    function convert_utc_to_local(utc_dt) {
      utc_datetime = moment.utc(utc_dt);
      datetime = utc_datetime.local();
      return datetime.format('MMMM Do YYYY, H:mm:ss');
    }

    function guid() {
      // http://stackoverflow.com/a/105074
      function s4() {
        return Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1);
      }
      return s4() + s4() + '-' + s4() + '-' + s4() + '-' + s4() + '-' + s4() + s4() + s4();
    }

    function get_survey_data() {
      var data = $('#post-data').val();
      var obj = JSON.parse(data);

      // if no tx_id
      if (!("tx_id" in obj)) {
        // generate uuid
        obj["tx_id"] = guid();
      }

      // if no submitted_at
      if (!("submitted_at" in obj)) {
        // set as current date and time
        obj["submitted_at"] = moment.utc().format('YYYY-MM-DDTH:mm:ssZ')
      }
      return JSON.stringify(obj);
    }

    $('.utc_datetime').each(function(index, obj) {
      obj.innerHTML = convert_utc_to_local(obj.innerHTML);
    });

    $('ul.nav.nav-tabs li a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    });

    $('#submitter-form').on('submit', function(event){
        event.preventDefault();
        var postData = get_survey_data();
        var quantity = $('#survey-quantity').val();

        $.post('/', '{"survey": ' + postData + ', "quantity": ' + quantity + '}')
          .done(function(data){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Posted: " + data);
            $(".alert").show();
          })
          .fail(function(){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during submission");
            $(".alert").show();
          });
    });

    $('#decrypt-form').on('submit', function(event){
        event.preventDefault();
        var postData = get_survey_data();
        $.post('/decrypt', postData)
          .done(function(data){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Posted encrypted data: " + data.substr(1, 100) + "...");
            $(".alert").show();
          }, 'json')
          .fail(function(){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during submission");
            $(".alert").show();
          });
    });

    $('#validate').on('click', function(event){
        event.preventDefault();
        var postData = get_survey_data();
        $.post('/validate', postData)
          .done(function(data){
            console.log(data);
            $(".alert").removeClass('alert-success alert-danger hidden');
            if (data.valid === true) {
              $(".alert").addClass('alert-success').text("Validation result: " + JSON.stringify(data));
            } else {
              $(".alert").addClass('alert-danger').text("Validation Error. Result: " + JSON.stringify(data))
            }
            $(".alert").show();
          })
          .fail(function(){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during validation submission");
            $(".alert").show();
          });
    });

    var dataTypes = ['pck', 'image', 'index', 'receipt'];

    function pollFTP() {
      $.getJSON('/list', function(data) {
        for (var i in dataTypes) {
          var dataType = dataTypes[i];
          var tableData = data[dataType];

          $("#" + dataType + "-data tbody").empty();

          $.each(tableData, function(filename, metadata){
            var $tableRow = $('<tr id="' + metadata['filename'] + '"><td><a href="#">' + metadata['filename'] + '</a></td><td>' +  metadata['size'] + '</td><td>' + convert_utc_to_local(metadata['modify']) + '</td></tr>');

            var onClickType = dataType;

            $tableRow.on("click", function(event){
              var filename = $(event.target).closest("tr").attr("id");

              $('#contentModal .modal-title').text(filename);

              $.get('/view/' + onClickType + '/' + filename, function(data){
                $('#contentModal .modal-body').html(data);
                $('#contentModal').modal('show');
              });
            });

            $("#" + dataType + "-data tbody").append($tableRow);
          });
        }
      });
    }

    $.get('/surveys/0.ce2016.json', function(data){
      $("#post-data").text(data);
    });

    $("#survey-selector").on("change", function(event){
      $.get('/surveys/' + $(event.target).val(), function(data){
        $("#post-data").text(data);
      });
    });

    $("#empty-ftp").on("click", function(event){
      $.getJSON('/clear')
        .done(function(data){

          for (var i in dataTypes) {
            var dataType = dataTypes[i];

            $("#" + dataType + "-data tbody").empty();
          }

          $(".alert").removeClass('alert-success alert-danger hidden');
          $(".alert").addClass('alert-success').text("Cleared " + data.removed + " files from FTP");
          $(".alert").show();
        })
        .fail(function(){
          $(".alert").removeClass('alert-success alert-danger hidden');
          $(".alert").addClass('alert-danger').text("Error on emptying ftp");
          $(".alert").show();
        });
    });

    $(".btn-reprocess").on("click", function(event){
      var id = $(this).data("id");
      $.post('/store', id)
          .done(function(data){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Survey " + data + " queued for processing");
            $(".alert").show();
          })
          .fail(function(){
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error queuing survey");
            $(".alert").show();
          });
    });

    setInterval(pollFTP, 2000);
});
