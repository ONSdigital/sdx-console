$(function(){
    $('form').on('submit', function(event){
        event.preventDefault();

        $.ajax({
          type: "POST",
          url: "/submitter",
          data: $('#post-data').val()
        });
    });
});