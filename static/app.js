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
      $.get('/viewer', function(data) {
        $("#response-data textarea").empty();
        $("#response-data textarea").text(data);
      });
    }

    setInterval(pollFTP, 2000);
});