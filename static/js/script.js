var elems;
var instances;
var currYear = (new Date()).getFullYear();    

$(document).ready(function(){
    //$('select').formSelect();
    M.updateTextFields();
    elems = document.querySelectorAll('select');
    $('#years').on('change', function() {
        console.log('change registered.')
        console.log($(this).val())
        let year=$(this).val();
        getFilm(year);
    });
    $('.carousel.carousel-slider').carousel({
        fullWidth: true,
    });        
    $('.prev').click(function(){
        $('.carousel').carousel('prev');
    });
    $('.next').click(function(){
        $('.carousel').carousel('next');
    });
    $('.modal').modal();
    let tpBtnCount=$('.top-picks > .page-btn').length;
    let nrBtnCount=$('.new-releases > .page-btn').length;
    console.log(tpBtnCount)
    console.log(nrBtnCount)
    // eliminates chevrons where only one page exists within pagination.
    if (tpBtnCount==1){ 
        $(".top-picks .left-chev").hide();
        $(".top-picks .right-chev").hide();
    }
    if (nrBtnCount==1){ 
        $(".new-releases .left-chev").hide();
        $(".new-releases .right-chev").hide();
    }
});

// Index.html
function checkPasswordsMatch(input) {
    console.log('checker function accessed.')
    if ( $('#c_password').val() != $('#password').val() && $('#c_password').val().length>0 ) {
        console.log('passwords not equal accessed.\n'+$('#password').val()+' , '+input.value)
        $("div #err-msg").html("Password Must be Matching.");
        $("#err-msg").css("color","red");
    } else {
        // input is valid -- reset the error message
        console.log('passwords equal accessed.\n'+$('#password').val()+' , '+input.value)
        $("#err-msg").html("<p></p>");
    }
}

//  Userprofile
    function getSuggestions(filmname){
        $.get('https://www.omdbapi.com/?s='+filmname.value+'&apikey=61e49492',function(rawdata){
            console.log('getSuggestions entered.')
            /**** clear previous suggestions ****/
            var title_object = {};
            /**** autocomplete film suggestions ****/
            for (film of rawdata.Search){
                title_object[film.Title] = null;
            }

            $('input.autocomplete').autocomplete({
                data: title_object,
                limit: 5
            });  
        }); 
    }  
           
	function getFilms(filmname){
	    $.get('https://www.omdbapi.com/?s='+filmname.value+'&apikey=61e49492',function(rawdata){
            /**** clear previous search data ****/
            $("#film-display").html("");
            $('#years').html(`<option value="" disabled selected>Choose which year</option>`);
            $('#imdbID').html(`<option value="" disabled selected>Imdb ID</option>`);
            var year_object = {};
	        var arrayNoDuplicatesID = [];
	        var id = 0;
	        for ( film of rawdata.Search){
	            if (filmname.value.toLowerCase()===film.Title.toLowerCase() && arrayNoDuplicatesID.indexOf(film.imdbID)===-1 && film.Type==='movie'){
	                console.log("condition accessed.")
                    year_object[film.Year] = null;
                    id++;
                    $("#film-display").append(`<div class="film-data" id="`+film.imdbID+`"><img src="`+film.Poster+`"/><p>"`+film.Title+`", `+film.Year+`, `+film.imdbID+`</p></div>`);
                    arrayNoDuplicatesID.push(film.imdbID);
                    }
            }
            if (id===0){
                $("#film-display").html("<p>Unfortunately this film doesn't exist in our database.</p>")
            }
            
             $('#film-display > div').on('click', function() {
                console.log('click registered.')
                //console.log($(this).id)
                console.log('id is '+this.id)
                getFilm(this.id);
            });
	    });
    }

    function getFilm(chosen_id) {
        console.log('getFilm accessed.')
        let film_title=$('#film_title').val();
        $('select').formSelect();
	    $.get('https://www.omdbapi.com/?i='+chosen_id+'&apikey=61e49492',function(rawdata){
            //$("#film-display").html("");
            let arrayNoDuplicatesID=[];
            var rawstring=JSON.stringify(rawdata);
            omdb_data = JSON.parse(rawstring)
            console.log('rawstring is ' +rawstring+', Actors = '+rawdata["Actors"]+' Director = '+rawdata["Director"]+' runtime= '+rawdata["Runtime"])           
                
                if (arrayNoDuplicatesID.indexOf(rawdata["imdbID"])===-1){
                        //$("#film-display").html(`<div class="film-data" id="title1"><img src="`+film.Poster+`"/><p>"`+film.Title+`", `+film.Year+`, `+film.imdbID+`</p></div>`);
                    let fields=["imdbID","Year","Director","Actors","Runtime"];
                    for ( f of fields)
                        createElem(f, chosen_id);
                        arrayNoDuplicatesID.push(film.imdbID);
                }

        });
    }
    function createElem(parentNode, film_id) {
        $.get('https://www.omdbapi.com/?i='+film_id+'&apikey=61e49492',function(rawdata){
            console.log(parentNode)
            $("#"+parentNode).empty();
            let option=document.createElement("OPTION");
            // Create a "class" attribute
            let att = document.createAttribute("value");       
            // Set the value of the class attribute
            att.value = rawdata[parentNode];                           
            option.setAttributeNode(att);                  
            //option.attr({value: rawdata[parentNode], disabled: "disabled", selected: "selected");
            console.log(parentNode+' is '+option.value)
            option.innerHTML=rawdata[parentNode];
            document.getElementById(parentNode).appendChild(option);
        });
    }
    function confirmDelete(film){
        let filmId=film.id.slice(4);
        let filmTitle=$('#title-'+filmId).text();
        let filmYear=$('#year-'+filmId).text();
        $('#del-msg').html("Delete review for "+filmTitle+" ("+filmYear+") ?");
        $('#modal1').modal('open');
        $('#del-btn').attr("href", $SCRIPT_ROOT+'/delete_rating/'+filmId); 
    }

//  Userview 

    function getPage(pageButton){
        if ($(pageButton).parent().hasClass('top-picks')){
            $(".top-picks.film-card-container").hide();
        }
        if ($(pageButton).parent().hasClass('new-releases')){
            $(".new-releases.film-card-container").hide();
        }
        let pageLink=$(pageButton).children('a').attr('href');
        /* The link attribute is the same as the id of its associated page table.*/
        $(pageLink).css('display', 'grid');
    }

    function updateChevronState(activeBtnId){
        let tpPageBtnCount=$('.top-picks > li').length-2;
        let nrPageBtnCount=$('.new-releases > li').length-2;

        /* Determine chevron states to be disabled or not - applies to prevPage() and nextPage() also  --> refactor / on doc ready */
        /* Top-pick Chevrons */
        if (activeBtnId=="tp-page-btn1"){
            $('.top-picks .right-chev').removeClass("disabled");
            $('.top-picks .left-chev').addClass("disabled");
        } else if (activeBtnId=="tp-page-btn"+tpPageBtnCount){
            $('.top-picks .left-chev').removeClass("disabled");
            $('.top-picks .right-chev').addClass("disabled");
        } else if (activeBtnId.slice(0,11)=='tp-page-btn'){    /* Both chevrons enabled */
            $('.top-picks .left-chev').removeClass("disabled");
            $('.top-picks .right-chev').removeClass("disabled");
        }
        /* New-releases Chevrons */
        if (activeBtnId=="nr-page-btn1"){
            $('.new-releases .right-chev').removeClass("disabled");
            $('.new-releases .left-chev').addClass("disabled");
        } else if (activeBtnId=="nr-page-btn"+nrPageBtnCount){
            $('.new-releases .left-chev').removeClass("disabled");
            $('.new-releases .right-chev').addClass("disabled");
        } else if(activeBtnId.slice(0,11)=='nr-page-btn'){    /* Both chevrons enabled */
            $('.new-releases .left-chev').removeClass("disabled");
            $('.new-releases .right-chev').removeClass("disabled");
        }
    }

    function goToPage(page){
        getPage(page);
        if ($(page).parent().hasClass('top-picks')){
            $('.top-picks > li').removeClass('active');
        }
        if ($(page).parent().hasClass('new-releases')){
            $('.new-releases > li').removeClass('active');
        }
        $(page).addClass("active");
        let activeBtnId=$(page).attr("id");
        updateChevronState(activeBtnId);  
    }

    function getCurrentBtn(paginationClass){
        // Retrieves the page button with active status (currently displaying that number page of results) 
        // paginationClass distinguishes the sets of buttons being dealth with.
        let currentBtnId;
        let pageBtns=$('.pagination'+paginationClass).children().each(function(){
            if($(this).hasClass('active')){
                currentBtnId=$(this).attr('id');
            }
            return currentBtnId;
        });
        return currentBtnId;
    }

    function prevPage(chevron) {
        let isTopPicks=$(chevron).parent().hasClass('top-picks');
        let isNewRelease=$(chevron).parent().hasClass('new-releases');
        /* if chevron btn enabled allow prev function to be carried out */
        if (!$(chevron).hasClass("disabled") ){
            let currentBtnId, prevBtnId;

            if (isTopPicks){
                currentBtnId=getCurrentBtn('.top-picks');
                // Extracts number from page button Id and decrements by 1 to establish previous page.
                prevBtnId='tp-page-btn'+(String(currentBtnId).match(/\d+/)-1 ); 
            }
            if (isNewRelease){
                currentBtnId=getCurrentBtn('.new-releases');
                prevBtnId='nr-page-btn'+(String(currentBtnId).match(/\d+/)-1 );
            }
            $('#'+currentBtnId).removeClass('active');
            $('#'+prevBtnId).addClass('active');
            /* Change page table showing */
            getPage('#'+prevBtnId);
            updateChevronState(prevBtnId); 
        }
    }

    function nextPage(chevron) {
        let isTopPicks=$(chevron).parent().hasClass('top-picks');
        let isNewRelease=$(chevron).parent().hasClass('new-releases');
        /* if chevron btn enabled allow next function to be carried out */
        if (!$(chevron).hasClass("disabled")){
            let currentBtnId, nextBtnId;
            if (isTopPicks){
                currentBtnId=getCurrentBtn('.top-picks');
                // Extracts number from page button Id and decrements by 1 to establish previous page.
                nextBtnId='tp-page-btn'+(1+parseInt(String(currentBtnId).match(/\d+/)) ); 
            }
            if (isNewRelease){
                currentBtnId=getCurrentBtn('.new-releases');
                nextBtnId='nr-page-btn'+(1+parseInt(String(currentBtnId).match(/\d+/) ) );
            }
            console.log('nextBtnId is '+nextBtnId)
            $('#'+currentBtnId).removeClass('active');
            $('#'+nextBtnId).addClass('active');
            /* Change page table showing */
            getPage('#'+nextBtnId);
            updateChevronState(nextBtnId); 
        }
    }

// films.html

function getGenre(genre){
    let genreToQuery = $(genre).html(); 
    $.getJSON($SCRIPT_ROOT + '/show_genre_films', { genre: genreToQuery },
    function(data) {
        let r = data.result;
        console.log("retrieval success")
        r=JSON.parse(r);
        console.log('result is of type '+typeof(r))
        $("#genre-table").empty();
        $("#genre-top-10").html(genreToQuery+" Top 10");
        for(let i=0; i<r.length; i++){
            $("#genre-table").append(`
            <a class="table-row film-card" href="`+$SCRIPT_ROOT+`/get_reviews/`+r[i].imdbID+`/`+r[i].averageRating+`">
                <div class="table-cell rank">`+(i+1)+`</div>
                <div class="table-cell title">`+r[i].title+`</div>
                <div class="table-cell year">`+r[i].year+`</div>
                <div class="table-cell avg-rating">`+r[i].averageRating+`</div>
                <div class="table-cell ratings-count">(`+r[i].ratingsCount+` ratings)</div>    
            </a>`)
        }
    });
}

function getDirectors(){
    let directorToQuery = $("#director_name").val();
    $.getJSON($SCRIPT_ROOT + '/show_director_films', 
        { director: directorToQuery },
        function(data) {
            let r = data.result;
            console.log("retrieval success")
            r=JSON.parse(r);
            $("#director-table").empty();
            $('#director-error').empty();
            if (r.length===0){
                $('#director-error').html("Sorry but there are no films by this director on our records.")
            } else {
                $("#director-top-10").html(formatDirectorInput(directorToQuery)+"'s Top 10");
                for(let i=0; i<r.length; i++){
                    $("#director-table").append(`
                    <a class="table-row film-card" href="`+$SCRIPT_ROOT+`/get_reviews/`+r[i].imdbID+`/`+r[i].averageRating+`">
                        <div class="table-cell rank">`+(i+1)+`</div>
                        <div class="table-cell title">`+r[i].title+`</div>
                        <div class="table-cell year">`+r[i].year+`</div>
                        <div class="table-cell avg-rating">`+r[i].averageRating+`</div>
                        <div class="table-cell ratings-count">(`+r[i].ratingsCount+` ratings)</div>    
                    </a>`
                )
            }
        }
    }); 
}    

function formatDirectorInput(directorName){
    // formats input to 
    directorName=directorName.toLowerCase();
    directorWords=directorName.split(" ");
    formattedWords=[];
    for(word of directorWords){
        word=word.charAt(0).toUpperCase()+word.slice(1);
        formattedWords.push(word);
    }
    formattedDirectorName=formattedWords.join(" ");
    return formattedDirectorName;
}

function getDecade(year){
    let decadeToQuery = $(year).attr('id');
    decadeToQuery= parseInt(decadeToQuery);
    $.getJSON($SCRIPT_ROOT + '/show_decade_films', { decade: decadeToQuery },
        function(data) {
            let r = data.result;
            console.log("retrieval success")
            r=JSON.parse(r);
            $("#decade-table").empty();
            $("#decade-top-10").html(decadeToQuery+"'s Top 10");
            for(let i=0; i<r.length; i++){
                $("#decade-table").append(`
                <a class="table-row film-card" href="`+$SCRIPT_ROOT+`/get_reviews/`+r[i].imdbID+`/`+r[i].averageRating+`">
                    <div class="table-cell rank">`+(i+1)+`</div>
                    <div class="table-cell title">`+r[i].title+`</div>
                    <div class="table-cell year">`+r[i].year+`</div>
                    <div class="table-cell avg-rating">`+r[i].averageRating+`</div>
                    <div class="table-cell ratings-count">(`+r[i].ratingsCount+` ratings)</div>    
                </a>`
            )
        }
    }); 
} 
   