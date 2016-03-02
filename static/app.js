$(function(){
    $('form').on('submit', function(event){
        event.preventDefault();
        var postData = $('#post-data').val();

        $.post('/submitter', $('#post-data').val())
          .done(function(data){
            $("#response-data").text("Posted: " + data);
          })
          .fail(function(){
            $('#response-data').text("Error during submission");
          })
    });
});