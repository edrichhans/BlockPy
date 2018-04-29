var HttpClient = function() {
    this.get = function(aUrl, aCallback) {
        var anHttpRequest = new XMLHttpRequest();
        anHttpRequest.onreadystatechange = function() { 
            if (anHttpRequest.readyState == 4 && anHttpRequest.status == 200)
                aCallback(anHttpRequest.responseText);
        }
        anHttpRequest.open( "GET", aUrl, true );            
        anHttpRequest.send( null );
    }
    this.post = function(url, data, callback) {
        var xhr = new XMLHttpRequest();
        
        xhr.onreadystatechange = function () {
            var readyState = xhr.readyState;

            if (readyState == 4) {
                callback(xhr);
            }
        };
        
        var queryString = '';
        if (typeof data === 'object') {
            for (var propertyName in data) {
                queryString += (queryString.length === 0 ? '' : '&') + propertyName + '=' + encodeURIComponent(data[propertyName]);
            }
        }
        
        xhr.open('POST', url, true);
        xhr.setRequestHeader('content-type', 'application/x-www-form-urlencoded');
        xhr.send(queryString);
    }
}

function promiseGet(client, url) {
    return new Promise ((resolve, reject) => {
        client.get(url, res => {
            if (res != null) {
                resolve(res);
            }
            else reject('GET returned NULL');
        });
    });
}

function promisePost(client, url, data) {
    return new Promise ((resolve, reject) => {
        client.post(url, data, res => {
            if (res != null) {
                resolve(res.responseText);
            }
            else reject('POST returned NULL');
        })
    })
}

var client = new HttpClient();
client.get('http://localhost:5002/blocks', function(response) {
    var blocks = JSON.parse(response)['chain'];
    for (var i = blocks.length - 1; i >= 0; i--) {
        $('#block-container').append('<div class="two wide column" id="block' + (i+1) + '">' + '<div class="ui ignored message myBlock"' + ' data-title="' + blocks[i]['timestamp'] + '" data-content="Block Hash: ' + blocks[i]['block_hash'] + '\nTxn: ' + blocks[i]['block_txn'] + '">' + blocks[i]['block_number'] + '</div></div>');
    }
    $('.myBlock')
        .popup({
            boundary: '#main',
            lastResort: 'bottom left',
        })
        .click(function() {
            $('.ui.modal.block p.block_content').text($(this).data('content'))
            $('.ui.modal.block .header').text($(this).data('title'))
            $('.ui.modal.block')
                .modal('show');
        });
});

promiseGet(client, 'http://localhost:5002/txns')
    .then(data => {
        var txns = JSON.parse(data)['txns'];
        for (var i = txns.length - 1; i >= 0; i--) {
            $('#txn-body').append('<tr data-title="Transaction number: ' + txns[i]['txn_number'] + '" data-content="Content: ' + eval(txns[i]['txn_content']['_content']) + '\nOwner: ' + txns[i]['txn_content']['_owner'] + '\nRecipient: ' + txns[i]['txn_content']['_recipient'] + '" id="txn' + (i+1) + '""><td>' + txns[i]['txn_number'] + '</td><td>' + txns[i]['block_number'] + '</td><td>' + txns[i]['timestamp'] + '</td><td class="content">' + txns[i]['txn_content']['_content'] + '</td><td class="owner">' + txns[i]['txn_content']['_owner'] + '</td><td class="recipient">' + txns[i]['txn_content']['_recipient'] + '</td></tr>')
            $('#txn'+(i+1))
            .popup({
                // boundary: 'body',
                lastResort: 'bottom left',
                onshow: function() {
                    resizePopup();
                }
            })
            .click(function() {
                $('.ui.modal.txn p.txn_content').text($(this).data('content'));
                $('.ui.modal.txn .header').text($(this).data('title'));
                $('.ui.modal.txn')
                    .modal('show');
            });
        }
        return txns;
    })
    .then(txns => {
        var i = 0;
        for (i = txns.length - 1; i >= 0; i--) {
            promisePost(client, 'http://localhost:5002/verify', {'txn': txns[i]['txn_number']})
                .then(data => {
                    data = JSON.parse(data);
                    $('tr#txn' + Object.keys(data)[0]).append('<td class="verified">' + data[Object.keys(data)[0]] + '</td>');
                })
                .catch(error => console.log(error));
        }
    })
    .catch(error => console.log(error))

promiseGet(client, 'http://localhost:5002/peers')
    .then(data => {
        var peers = JSON.parse(data);
        for (var i = peers.length - 1; i >= 0; i--) {
            $('tbody#peers-body').append('<tr><td>' + peers[i][0] + '</td><td>' + peers[i][1] + '</td></tr>');
        }
    })

var resizePopup = function(){$('.ui.popup').css('max-height', $(window).width());};

$(window).resize(function(e){
    resizePopup();
});

$('i.bars.icon').click(function() {
    $('.ui.sidebar')
        .sidebar('toggle')
    ;
});

$('.menu .item')
    .tab()
;


$('.ui.form')
    .form({
        fields: {
            content: {
                identifier: 'content',
                rules: [
                    {
                        type: 'empty',
                        prompt: 'Please input a valid a transaction.'
                    }
                ]
            }
        }
    })
;

$("form#insert").submit(function(e) {
    e.preventDefault();
    $.ajax({
        type: "POST",
        url: "http://localhost:5002/insert",
        data: $(this).serialize(),
        success: function(res) {
            console.log(res);
            window.location.replace("http://localhost:8080");
            $('.ui.tab#home').removeClass('active');
            $('.ui.tab#insert').addClass('active');
        },
        error: {
            function(err) {
                console.log(err);
            }
        }
    });
});



