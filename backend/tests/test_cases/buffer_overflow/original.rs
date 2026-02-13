// Vulnerable: Buffer overflow - direct array access without bounds checking
fn get_element(arr: &[i32], index: usize) -> i32 {
    unsafe {
        *arr.get_unchecked(index)
    }
}

fn main() {
    let numbers = [1, 2, 3, 4, 5];
    println!("Element: {}", get_element(&numbers, 10));
}
