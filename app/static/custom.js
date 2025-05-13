let edit_func = async (api, datatable, method, fields) => {

    let formData = new FormData();

    for (const [key, value] of Object.entries(fields)) {
        if (value.input.getAttribute('type') == "checkbox") {
            formData.append(key, value.input.checked);
        }
        else {
            formData.append(key, value.input.value);
        }
    }

    const response = await fetch(api, {
        method: method,
        body: formData,
    })

    if (response.ok) {
        dlg.close();
        await response.json().then((data) => {
            $.alert(data.message);
        })
        datatable.ajax.reload(null, false);
    } else {
        const errors = await response.json();
        Object.keys(errors).forEach((key) => {
            fields[key].input.classList.add('is-invalid');
            fields[key].error.innerHTML = errors[key][0];
        });
    }
}