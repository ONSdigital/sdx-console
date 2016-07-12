$(function(){
    $('ul.nav li a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    });

    $('#submitter-form').on('submit', function(event){
        event.preventDefault();
        var postData = $('#post-data').val();
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
        var postData = $('#post-data').val();

        $.post('/decrypt', $('#post-data').val())
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
        var postData = $('#post-data').val();
        $.post('/validate', $('#post-data').val())
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
            var $tableRow = $('<tr id="' + metadata['filename'] + '"><td><a href="#">' + metadata['filename'] + '</a></td><td>' +  metadata['size'] + '</td><td>' + metadata['modify'] + '</td></tr>');

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

    $.get('/surveys/023.0102.json', function(data){
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
