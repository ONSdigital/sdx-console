$(function () {

    function asyncGet(url) {
        // Return a new promise.
        return new Promise(function (resolve, reject) {
            // Do the usual XHR stuff
            var req = new XMLHttpRequest();
            req.open('GET', url);

            req.onload = function () {
                // This is called even on 404 etc
                // so check the status
                if (req.status == 200) {
                    // Resolve the promise with the response text
                    resolve(req.response);
                }
                else {
                    // Otherwise reject with the status text
                    // which will hopefully be a meaningful error
                    reject(Error(req.statusText));
                }
            };

            // Handle network errors
            req.onerror = function () {
                reject(Error("Network Error"));
            };

            // Make the request
            req.send();
        });
    }

    function asyncGetJSON(url) {
        return asyncGet(url).then(JSON.parse);
    }

    function convert_utc_to_local(utc_dt) {
        if (!utc_dt) {
            return '';
        }
        utc_datetime = moment.utc(utc_dt);
        datetime = utc_datetime.local();
        // return datetime.format('MMMM Do YYYY, H:mm:ss');
        return datetime.format('Y-m-d H:mm:ss');
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
            obj["submitted_at"] = moment.utc().format('YYYY-MM-DDTHH:mm:ssZ')
        }
        return JSON.stringify(obj, undefined, 1);
    }

    $('.utc_datetime').each(function (index, obj) {
        obj.innerHTML = convert_utc_to_local(obj.innerHTML);
    });

    $('ul.nav.nav-tabs li a').click(function (e) {
        e.preventDefault()
        $(this).tab('show')
    });

    $('#submitter-form').on('submit', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        var quantity = $('#survey-quantity').val();

        $.post('/', '{"survey": ' + postData + ', "quantity": ' + quantity + '}')
            .done(function (data) {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-success').text("Posted: " + data);
                $(".alert").show();
            })
            .fail(function () {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-danger').text("Error during submission");
                $(".alert").show();
            });
    });

    $('#decrypt-form').on('submit', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        $.post('/decrypt', postData)
            .done(function (data) {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-success').text("Posted encrypted data: " + data.substr(1, 100) + "...");
                $(".alert").show();
            }, 'json')
            .fail(function () {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-danger').text("Error during submission");
                $(".alert").show();
            });
    });

    $('#validate').on('click', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        $.post('/validate', postData)
            .done(function (data) {
                console.log(data);
                $(".alert").removeClass('alert-success alert-danger hidden');
                if (data.valid === true) {
                    $(".alert").addClass('alert-success').text("Validation result: " + JSON.stringify(data));
                } else {
                    $(".alert").addClass('alert-danger').text("Validation Error. Result: " + JSON.stringify(data))
                }
                $(".alert").show();
            })
            .fail(function () {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-danger').text("Error during validation submission");
                $(".alert").show();
            });
    });

    // function getFTP() {
    //
    //     $.getJSON('/list', function (data) {
    //         for (var i in dataTypes) {
    //             var dataType = dataTypes[i];
    //             var tableData = data[dataType];
    //
    //             $("#" + dataType + "-data tbody").empty();
    //
    //             $.each(tableData, function (filename, metadata) {
    //                 var $tableRow = $('<tr id="' + metadata['filename'] + '"><td><a href="#">' + metadata['filename'] + '</a></td><td>' + metadata['size'] + '</td><td>' + convert_utc_to_local(metadata['modify']) + '</td></tr>');
    //
    //                 var onClickType = dataType;
    //
    //                 $tableRow.on("click", function (event) {
    //                     var filename = $(event.target).closest("tr").attr("id");
    //
    //                     $('#contentModal .modal-title').text(filename);
    //
    //                     $.get('/view/' + onClickType + '/' + filename, function (data) {
    //                         $('#contentModal .modal-body').html(data);
    //                         $('#contentModal').modal('show');
    //                     });
    //                 });
    //
    //                 $("#" + dataType + "-data tbody").append($tableRow);
    //             });
    //         }
    //     });
    //
    // }

    // $("#refresh-ftp").on("click", function (event) {
    //     $("#refresh-ftp").button('loading');
    //     getFTP();
    //     $("#refresh-ftp").button('reset');
    // });

    // $.get('/surveys/0.ce2016.json', function (data) {
    //     $("#post-data").text(data);
    // });

    $("#survey-selector").on("change", function (event) {
        $.get('/surveys/' + $(event.target).val(), function (data) {
            $("#post-data").text(data);
        });
        // asyncGet('/view/' + onClickType + '/' + filename).then(function (data) {
        //     $('#contentModal .modal-body').html(data);
        //     $('#contentModal').modal('show');
        // }, function (error) {
        //     console.error("Failed!", error);
        // });
    });

    // $("#empty-ftp").on("click", function (event) {
    //     $.getJSON('/clear')
    //         .done(function (data) {
    //
    //             for (var i in dataTypes) {
    //                 var dataType = dataTypes[i];
    //
    //                 $("#" + dataType + "-data tbody").empty();
    //             }
    //
    //             $(".alert").removeClass('alert-success alert-danger hidden');
    //             $(".alert").addClass('alert-success').text("Cleared " + data.removed + " files from FTP");
    //             $(".alert").show();
    //         })
    //         .fail(function () {
    //             $(".alert").removeClass('alert-success alert-danger hidden');
    //             $(".alert").addClass('alert-danger').text("Error on emptying ftp");
    //             $(".alert").show();
    //         });
    // });

    $(".btn-reprocess").on("click", function (event) {
        var id = $(this).data("id");
        $.post('/store', id)
            .done(function (data) {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-success').text("Survey " + data + " queued for processing");
                $(".alert").show();
            })
            .fail(function () {
                $(".alert").removeClass('alert-success alert-danger hidden');
                $(".alert").addClass('alert-danger').text("Error queuing survey");
                $(".alert").show();
            });
    });
    //
    // // getFTP();
    //
    // // setInterval(pollFTP, 2000);

    // function enable_ftp_data_stream() {
    //
    //     // reset the event stream connection:
    //     try {
    //         $source.close();
    //     } catch(err) {}
    //     $source = new EventSource("/ftpstream");
    //
    //     $source.addEventListener('message', function(e) {
    //         var data = JSON.parse(e.data);
    //         for (var i in dataTypes) {
    //             var dataType = dataTypes[i];
    //             var tableData = data[dataType];
    //
    //             $("#" + dataType + "-data tbody").empty();
    //
    //             $.each(tableData, function (filename, metadata) {
    //                 var $tableRow = $('<tr id="' + metadata['filename'] + '"><td><a href="#">' + metadata['filename'] + '</a></td><td>' + metadata['size'] + '</td><td>' + convert_utc_to_local(metadata['modify']) + '</td></tr>');
    //
    //                 var onClickType = dataType;
    //
    //                 $tableRow.on("click", function (event) {
    //                     var filename = $(event.target).closest("tr").attr("id");
    //
    //                     $('#contentModal .modal-title').text(filename);
    //
    //                     $.get('/view/' + onClickType + '/' + filename, function (data) {
    //                         $('#contentModal .modal-body').html(data);
    //                         $('#contentModal').modal('show');
    //                     });
    //                 });
    //
    //                 $("#" + dataType + "-data tbody").append($tableRow);
    //             });
    //         }
    //     }, false);
    //
    // }
    //
    // // set event stream connection global:
    // var $source;
    //
    // // reset the event stream connection
    // enable_ftp_data_stream();
    //
    // setInterval(enable_ftp_data_stream, 60000);
    //
    // window.addEventListener("beforeunload", function(event) {
    //     // free up the connection:
    //     try {
    //         $source.close();
    //     } catch(err) {}
    // });

    asyncGet('/surveys/0.ce2016.json').then(function (response) {
        $("#post-data").text(response);
    }, function (error) {
        console.error("Failed!", error);
    });

    var dataTypes = ['pck', 'image', 'index', 'receipt'];

    function refreshFTP() {
        $('#ftp-loading-sign').show();
        asyncGetJSON('/ftp.json').then(function (ftpData) {

            for (var i in dataTypes) {
                var dataType = dataTypes[i];
                var tableData = ftpData[dataType];

                $("#" + dataType + "-data tbody").empty();

                $.each(tableData, function (filename, metadata) {
                    var $tableRow = $('<tr id="' + metadata['name'] + '"><td><a href="#">' + metadata['name'] + '</a></td><td>' + metadata['size'] + 'b</td><td>' + metadata['modify'] + '</td></tr>');

                    var onClickType = dataType;

                    $tableRow.on("click", function (event) {
                        var filename = $(event.target).closest("tr").attr("id");
                        $('#contentModal .modal-title').text(filename);
                        asyncGet('/view/' + onClickType + '/' + filename).then(function (data) {
                            $('#contentModal .modal-body').html(data);
                            $('#contentModal').modal('show');
                        }, function (error) {
                            console.error("Failed!", error);
                        });
                    });

                    $("#" + dataType + "-data tbody").append($tableRow);
                });
            }

            setTimeout(refreshFTP, 2000);

        }, function (error) {
            $('#ftp-loading-sign').show();
            console.error("Failed!", error);
        });
    }

    // kick off the ftp polling
    refreshFTP();

});
