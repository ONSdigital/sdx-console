$(function(){
    $('form').on('submit', function(event){
        event.preventDefault();
        var postData = $('#post-data').val();

        $.post('/', $('#post-data').val())
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

    function pollFTP() {
      $.getJSON('/list', function(data) {
        $("#response-data tbody").empty();

        $.each(data, function(filename, metadata){
          $("#response-data tbody").append('<tr id="' + metadata['filename'] + '"><td><a href="#">' + metadata['filename'] + '</a></td><td>' +  metadata['size'] + '</td><td>' + metadata['modify'] + '</td></tr>');
        });

        $("tbody tr").on("click", function(event){
          var filename = $(event.target).closest("tr").attr("id");

          $('#contentModal .modal-title').text(filename);

          $.get('/view/' + filename + '?cb=' + Date.now(), function(data){
            $('#contentModal .modal-body').html(data);
            $('#contentModal').modal('show');
          });
        });
      });
    }

    $("#empty-ftp").on("click", function(event){
      $.getJSON('/clear')
        .done(function(data){
          $("#response-data tbody").empty();

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

    setInterval(pollFTP, 2000);
});