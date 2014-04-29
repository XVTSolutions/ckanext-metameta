
(function () {
    $(document).ready(function () {
        var removeOption = function(){
            //click "-" icon on option field
            $(".option_container .icon-minus-sign").on("click", function(event){
                //find option_group
                var num = $(this).closest("div.option_group").find(".option_container").length;
                if(num==1){
                    //clear value
                    $(this).closest(".option_container").find("input:text").val("");
                }else{
                    //remove element
                    $(this).closest(".option_container").remove();
                }
            });
        };
        var optimize_fields = function(){
            $("input:text").each(function(index, value){
                if(!$(this).attr("readonly")){
                    //trim
                    $(this).val($(this).val().trim());
                }
            });
            var num = $("div.option_group .option_container").length;
            $("div.option_group .option_container input:text").each(function(index, value){
                //empty and not last text is removed
                if(!(num == (index+1) || $(this).val().length)){
                    $(this).closest(".option_container").remove();
                }
            });
        };
        var validate_single_choice = function(){
            //check any valid options
            var option_texts = $("div.option_group .option_container input:text");
            var valid=false;
            for(var i=0; i<option_texts.length; i++){
                if($(option_texts[i]).val().length){
                    valid=true;
                    break;
                }
            }
            if(!valid){
                //error
                var container = $("div.option_group .option_container").append("<span class='error-block'></span>");
                $(container).find(".error-block").text("No valid option");
            }

            //if any checked option, add it as default value
            var checked_option_radio = $(".option_container input:radio:checked");
            if(checked_option_radio.length && $(checked_option_radio).closest(".option_container").find("input:text").val().length){
                var default_value = $(checked_option_radio).closest(".option_container").find("input:text").val();
                $("#field-default_value").val(default_value);
            }
            //set validator=not_empty
            if($("input:radio.validator:checked").val()!="not_empty"){
                $("input:radio.validator:checked").removeAttr("checked");
                $("input:radio.validator").each(function(index, value){
                    if($(this).val()=='not_empty'){
                        $(this).attr("checked", "checked");
                    }
                });
            }
        };
        var validate_range = function(){
            var minimum = $("#field-minimum");
            var maximum = $("#field-maximum");
            var default_value = $("#field-default_value");
            var error_count = 0;
            if(isNaN(parseFloat(minimum.val()))){
                //error
                var container = $(minimum).parent().append("<span class='error-block'></span>");
                $(container).find(".error-block").text("Only number is allowed to enter.");
                error_count++;
            }
            if(isNaN(parseFloat(maximum.val()))){
                //error
                var container = $(maximum).parent().append("<span class='error-block'></span>");
                $(container).find(".error-block").text("Only number is allowed to enter.");
                error_count++;
            }
            if(default_value.val().length && isNaN(parseFloat(default_value.val()))){
                //error
                var container = $(default_value).parent().append("<span class='error-block'></span>");
                $(container).find(".error-block").text("Only number is allowed to enter.");
                error_count++;
            }
            if(!error_count){
                if(parseFloat(maximum.val())<parseFloat(minimum.val())){
                    //error
                    var container = $(maximum).parent().append("<span class='error-block'></span>");
                    $(container).find(".error-block").text("The maximum value must be qual to or greater than the minumum one.");
                    container = $(minimum).parent().append("<span class='error-block'></span>");
                $(container).find(".error-block").text("The minumum value must be qual to or less than the maximum one.");
                }
                if(default_value.val().length){
                    if(parseFloat(default_value.val())<parseFloat(minimum.val())
                    || parseFloat(default_value.val())>parseFloat(maximum.val())){
                        //error
                        var container = $(default_value).parent().append("<span class='error-block'></span>");
                        $(container).find(".error-block").text("The default must be between the minimum and maximum values.");
                    }
                }
            }
        };
        var validate_default_value = function(){
            //if readonly and not ignore_missing and no default then error
            if($("input:radio.readonly:checked").val()=="True" && $("input:radio.validator:checked").val() != "ignore_missing"){
                if(!$("#field-default_value").val().trim().length){
                    //error
                    var container = $("#field-readonly").closest('.controls').append("<span class='error-block'></span>");
                    $(container).find(".error-block").text("Default Value must be set at readonly mode.");
                }
            }
        };
        $(".field_type").on("click", function(event){
            if(!$(this).attr("readonly")){
                if($(this).val()=="text"){
                    $(".field_type_text_or_area").show(500);
                    $(".field_type_single_choice").hide(500);
                    $("input:radio.validator:disabled[value='metameta_range']").removeAttr('disabled');
                    if($("input:radio.validator:checked").val()=="metameta_range"){
                        $(".range_group").show(500);
                    }
                }else if($(this).val()=="textarea"){
                    $(".field_type_text_or_area").show(500);
                    $(".field_type_single_choice").hide(500);
                    if($("input:radio.validator:checked").val()=="metameta_range"){
                        //remove checked from range validator
                        $("input:radio.validator:checked[value='metameta_range']").removeAttr("checked");
                        //set empty as checked
                        $("input:radio.validator[value='not_empty']").attr("checked", "checked");
                    }
                    $("input:radio.validator[value='metameta_range']").attr('disabled', 'disabled');
                    $(".range_group").hide(500);
                }else{
                    $(".field_type_text_or_area").hide(500);
                    $(".field_type_single_choice").show(500);
                    $(".range_group").hide(500);
                }
            }
        });
        $(".validator").on("click", function(event){
            if(!$(this).attr("readonly")){
                if($(this).val()=="metameta_range"){
                    $(".range_group").show(500);
                }else{
                    $(".range_group").hide(500);
                }
            }
        });
        //click "+" icon on option field
        $(".icon-plus-sign").on("click", function(event){
            //find option_group
            var val = $("div.option_group .option_container:last-child input:text").val();
            if(val.trim().length){
                //add new field
                $("div.option_group").append("<div class='option_container'> "+
            "<input id='field-default_value_radio' type='radio' title='Tick as a default value'  name='default_value_radio' "+ 
                    " class='' value='' placeholder=''/> "+
            "<input id='field-option_value' type='text' name='option_value[]' value='' "+
                    "placeholder='option_value'/> "+
            "<span class='btn btn-danger btn-small text-error icon-minus-sign' title='Delete'></span> "+
            "<div class='clearfix'></div></div><!--class='option_container'-->");
            }
            removeOption();
        })

        /*submit*/
        $("#submit_form").on("click", function(event){
            //remove errors
            $(".error-block").remove();
            //optimize fields
            optimize_fields();

            //dropdown list type
            if($("input:radio.field_type:checked").val()=="single_choice"){
                validate_single_choice();
            }

            //text type
            if($("input:radio.field_type:checked").val()=="text"){
                if($("input:radio.validator:checked").val()=="metameta_range"){
                    validate_range();
                }
            }
            //validate readonly
            validate_default_value();

            var ret = !($(".error-block").length)
            return ret;
        });
        removeOption();
    });

})();
