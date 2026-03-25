qui sysuse auto
qui sysuse auto
la var price "Price ($)"
desc
qui u SalaryCameron
qui drop in 1/100
des
gen ln_mpg = ln(mpg) // ln() is natural log function
reg price ln_mpg
