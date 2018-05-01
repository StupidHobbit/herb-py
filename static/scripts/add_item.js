var add = (function () {
    var counter = -1;
    return function () {return counter += 1;}
})();


var labels = [];
var ranges = [];
function add_item() {
    var tr = document.createElement("tr");
    var count = add();
    var div = document.getElementById("item_div");

    var td = document.createElement("td");
    var herb_input = document.createElement("input");
    herb_input.setAttribute("id", "herb_item" + count);
    herb_input.setAttribute("name", "herb_item"  + count);
    herb_input.setAttribute("type", "text");
    herb_input.setAttribute("maxlength", "40");
    herb_input.setAttribute("list", "herbs");
    td.appendChild(herb_input);
    tr.appendChild(td);

    td = document.createElement("td");
    var part_input = document.createElement("input");
    part_input.setAttribute("id", "part_item"  + count);
    part_input.setAttribute("name", "part_item"  + count);
    part_input.setAttribute("type", "text");
    part_input.setAttribute("maxlength", "40");
    part_input.setAttribute("list", "parts");
    td.appendChild(part_input);
    tr.appendChild(td);

    td = document.createElement("td");
    var perc_input = document.createElement("input");
    perc_input.setAttribute("id", "perc_item"  + count);
    perc_input.setAttribute("name", "perc_item"  + count);
    perc_input.setAttribute("type", "range");
    perc_input.setAttribute("maxlength", "40");
    perc_input.setAttribute("list", "tickmarks");
    perc_input.setAttribute("value", 0);
    //perc_input.setAttribute("step", 5);
    perc_input.setAttribute("onmousemove", "change_perc(" + count + ")");
    perc_input.setAttribute("onchange", "change_perc(" + count + ")");
    var perc_text = document.createElement("label");
    perc_text.setAttribute("for", "perc_item"  + count);
    perc_text.setAttribute("name", "perc_item"  + count);
    perc_text.innerText = "0";
    //perc_input.setAttribute("disabled", "1");
    labels.push(perc_text);
    ranges.push(perc_input);
    td.appendChild(perc_text);
    td.appendChild(perc_input);
    tr.appendChild(td);

    div.appendChild(tr);
}

function change_perc(n) {
    labels[n].innerText = ranges[n].value;
    var s = 0;
    for (i = 0; i < ranges.length; i++){
        s += Number(ranges[i].value);
    }
    var sum_text = document.getElementById("perc_sum");
    sum_text.innerText = s.toString();
    if (s == 100){
        sum_text.style.color = "Green";
        document.getElementById("submit").removeAttribute("disabled");
    } else{
        sum_text.style.color = "Red";
        document.getElementById("submit").setAttribute("disabled", "true");
    }
}