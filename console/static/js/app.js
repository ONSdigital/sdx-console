$(function () {

    function asyncGet(url) {
        // Return a new promise.
        return new Promise(function (resolve, reject) {
            // Do the usual XHR stuff
            var req = new XMLHttpRequest();
            req.open('GET', url, true);

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

    function asyncPostJSON(url, json_data) {
        // Return a new promise.
        return new Promise(function (resolve, reject) {
            // Do the usual XHR stuff
            var req = new XMLHttpRequest();
            req.open('POST', url, true);

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

            req.setRequestHeader("Content-Type", "application/json;charset=UTF-8");

            // Make the request
            req.send(JSON.stringify(json_data));
        });
    }

    function convert_utc_to_local(utc_dt) {
        if (!utc_dt) {
            return '';
        }
        utc_datetime = moment.utc(utc_dt);
        datetime = utc_datetime.local();
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
        return obj;
    }

    $('.utc_datetime').each(function (index, obj) {
        obj.innerHTML = convert_utc_to_local(obj.innerHTML);
    });

    $('ul.nav.nav-tabs li a').click(function (e) {
        e.preventDefault();
        $(this).tab('show');
    });

    $('#submitter-form').on('submit', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        var quantity = $('#survey-quantity').val();
        $(".alert").hide();
        asyncPostJSON('/', {
            "survey": postData,
            "quantity": quantity
        }).then(function (data) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Posted: " + data);
            $(".alert").show();
        }, function (error) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during submission");
            $(".alert").show();
            console.error("Failed!", error);
        });
    });

    $('#decrypt-form').on('submit', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        $(".alert").hide();
        asyncPostJSON('/decrypt', postData).then(function (data) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Posted encrypted data: " + data.substr(1, 100) + "...");
            $(".alert").show();
        }, function (error) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during submission");
            $(".alert").show();
            console.error("Failed!", error);
        });
    });

    $('#validate').on('click', function (event) {
        event.preventDefault();
        var postData = get_survey_data();
        $(".alert").hide();
        asyncPostJSON('/validate', postData).then(function (data) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            if (data.valid === true) {
                $(".alert").addClass('alert-success').text("Validation result: " + JSON.stringify(data));
            } else {
                $(".alert").addClass('alert-danger').text("Validation Error. Result: " + JSON.stringify(data))
            }
        }, function (error) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error during validation submission");
            $(".alert").show();
            console.error("Failed!", error);
        });
    });

    $("#survey-selector").on("change", function (event) {
        asyncGet('/surveys/' + $(event.target).val()).then(function (data) {
            $("#post-data").text(data);
        }, function (error) {
            console.error("Failed!", error);
        });
    });

    $("#empty-ftp").on("click", function (event) {
        $(".alert").hide();
        asyncGetJSON('/clear').then(function (data) {
            for (var i in dataTypes) {
                var dataType = dataTypes[i];
                $("#" + dataType + "-data tbody").empty();
            }
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-success').text("Cleared " + data.removed + " files from FTP");
            $(".alert").show();
        }, function (error) {
            $(".alert").removeClass('alert-success alert-danger hidden');
            $(".alert").addClass('alert-danger').text("Error on emptying ftp");
            $(".alert").show();
        });
    });

    $(".btn-reprocess").on("click", function (event) {
        $(".alert").hide();
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
                            console.error("FTP failed!", error);
                        });
                    });

                    $("#" + dataType + "-data tbody").append($tableRow);
                });
            }
            $('#ftp-loading-sign').hide();

            // recurse:
            setTimeout(refreshFTP, 2000);

        }, function (error) {
            $('#ftp-loading-sign').hide();
            console.error("FTP failed!", error);
        });
    }

    // on page load stuff:

    asyncGet('/surveys/0.ce2016.json').then(function (response) {
        $("#post-data").text(response);
    }, function (error) {
        console.error("Failed!", error);
    });

    asyncGetJSON('/surveys').then(function (surveys) {
        for (var i = 0; i < surveys.length; i++) {
            $('#survey-selector')
                .append($('<option>', {value: surveys[i]})
                    .text(surveys[i]));
        }
    }, function (error) {
        console.error("Failed!", error);
    });

    // kick off the ftp polling:
    refreshFTP();

});
